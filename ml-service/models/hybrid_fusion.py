"""
Context-Aware Weighted Ensemble Hybrid Anomaly Detector
Combines MSIF-LSTM and PLE-GRU with dynamic weighting

Key Features:
1. Dynamic weight calculation based on:
   - Time of day (peak hours vs off-hours)
   - Endpoint type (CPU-intensive vs API)
   - Traffic level (high vs low)

2. Confidence-based fusion strategies:
   - High agreement (>0.85): Weighted average
   - Moderate agreement (0.60-0.85): Conservative max
   - Low agreement (<0.60): Conflict detected (log warning)

3. Comprehensive monitoring:
   - Prediction count
   - Anomaly count
   - Model status tracking
   - Statistics per call

Production Ready:
- Error handling and logging
- Type hints on all methods
- Docstrings with examples
- Statistics tracking
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime
from src.logger import logger
from config.settings import config
from .msif_lstm_model import MSIFLSTM
from .ple_gru_model import PLEGRU

class HybridAnomalyDetector:
    """
    Context-Aware Weighted Ensemble Hybrid Anomaly Detector
    
    Combines two neural networks (MSIF-LSTM and PLE-GRU) with dynamic
    weight adjustment based on operational context.
    
    Workflow:
    1. Load pre-trained MSIF-LSTM and PLE-GRU models
    2. Make individual predictions
    3. Calculate context-aware weights
    4. Fuse predictions using confidence-based strategy
    5. Return combined score, severity, and metadata
    
    Attributes:
    - msif: MSIFLSTM instance
    - ple: PLEGRU instance
    - models_loaded: Boolean flag
    - prediction_count: Total predictions made
    - anomaly_count: Total anomalies detected
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize hybrid detector
        
        Args:
            model_path: Path to directory with trained models
                       (msif_lstm_model.h5, ple_gru_model.h5)
                       If None, models start untrained
        
        Example:
            >>> detector = HybridAnomalyDetector('./trained_models')
            >>> # Ready to predict
        """
        
        # Initialize individual models
        self.msif = MSIFLSTM()
        self.ple = PLEGRU()
        
        # Statistics
        self.models_loaded = False
        self.prediction_count = 0
        self.anomaly_count = 0
        
        # Try to load models if path provided
        if model_path:
            try:
                self.msif.load(model_path)
                self.ple.load(model_path)
                self.models_loaded = True
                logger.info("✅ Both models (MSIF-LSTM and PLE-GRU) loaded successfully")
            except Exception as e:
                logger.warning(
                    f"⚠️  Could not load models from {model_path}: {e}. "
                    f"Using untrained models."
                )
                self.models_loaded = False
        else:
            logger.warning("⚠️  No model path provided. Using untrained models.")
    
    # ============= MAIN PREDICTION =============
    
    def predict(self,
                features: np.ndarray,
                context: Optional[Dict] = None) -> Dict:
        """
        Make prediction with context-aware weighting
        
        Complete workflow:
        1. Validate input shape
        2. Get MSIF-LSTM and PLE-GRU predictions
        3. Calculate context-aware weights
        4. Fuse predictions based on model agreement
        5. Calculate severity and confidence
        6. Track statistics
        7. Return comprehensive result dict
        
        Args:
            features: np.ndarray of shape (10,) or (1, 10)
                     Normalized features from DataPreprocessor
            context: Optional dict with:
                - 'hour_of_day': 0-23
                - 'endpoint_type': 'api' or 'cpu_intensive'
                - 'traffic_level': 'high' or 'low'
        
        Returns:
            Dict with keys:
            - msif_score: MSIF-LSTM score [0-1]
            - ple_score: PLE-GRU score [0-1]
            - hybrid_score: Weighted ensemble score [0-1]
            - severity: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            - confidence: Model agreement [0-1]
            - weights_used: {'msif': float, 'ple': float}
            - fusion_method: Method used for fusion
            - models_loaded: Boolean
            - timestamp: ISO format UTC
            - stats: Prediction statistics
        
        Example:
            >>> features = np.array([0.5, 1.0, 0.6, ...])  # normalized
            >>> result = detector.predict(features, context={
            ...     'hour_of_day': 14,
            ...     'endpoint_type': 'api',
            ...     'traffic_level': 'high'
            ... })
            >>> print(f"Anomaly score: {result['hybrid_score']:.3f}")
            >>> print(f"Severity: {result['severity']}")
        """
        
        try:
            # Ensure correct shape
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Get individual model predictions
            msif_score = float(self.msif.predict(features)[0])
            ple_score = float(self.ple.predict(features)[0])
            
            logger.debug(f"Raw scores: MSIF={msif_score:.4f}, PLE={ple_score:.4f}")
            
            # Calculate context-aware weights
            weights = self._get_dynamic_weights(context or {})
            
            # Hybrid fusion
            hybrid_score, fusion_method = self._fuse_predictions(
                msif_score, ple_score, weights
            )
            
            # Calculate confidence based on model agreement
            model_agreement = 1.0 - abs(msif_score - ple_score)
            
            # Map to severity
            severity = config.get_severity(hybrid_score)
            
            # Update statistics
            self.prediction_count += 1
            if hybrid_score > config.THRESHOLDS.SEVERITY_LEVELS['MEDIUM']:
                self.anomaly_count += 1
            
            # Build result
            result = {
                'msif_score': msif_score,
                'ple_score': ple_score,
                'hybrid_score': hybrid_score,
                'severity': severity,
                'confidence': model_agreement,
                'weights_used': weights,
                'fusion_method': fusion_method,
                'models_loaded': self.models_loaded,
                'timestamp': datetime.utcnow().isoformat(),
                'stats': {
                    'total_predictions': self.prediction_count,
                    'anomalies_detected': self.anomaly_count,
                    'anomaly_rate': self.anomaly_count / max(self.prediction_count, 1)
                }
            }
            
            # Log result
            logger.info(
                f"Prediction: hybrid={hybrid_score:.3f}, "
                f"severity={severity}, confidence={model_agreement:.3f}, "
                f"method={fusion_method}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise
    
    # ============= WEIGHT CALCULATION =============
    
    def _get_dynamic_weights(self, context: Dict) -> Dict[str, float]:
        """
        Calculate context-aware weights for ensemble
        
        Blends weights based on three factors:
        1. Time of day (peak vs off-hours)
        2. Endpoint type (CPU-intensive vs API)
        3. Traffic level (high vs low)
        
        Blending formula: 50% base + 25% endpoint + 25% traffic
        
        Args:
            context: Dict with optional:
            - hour_of_day: 0-23 (default: 12)
            - endpoint_type: 'api' or 'cpu_intensive' (default: 'api')
            - traffic_level: 'high' or 'low' (default: 'medium')
        
        Returns:
            Dict {'msif': weight, 'ple': weight} where weights sum to 1.0
        
        Example:
            >>> weights = detector._get_dynamic_weights({
            ...     'hour_of_day': 14,
            ...     'endpoint_type': 'api',
            ...     'traffic_level': 'high'
            ... })
            >>> weights
            {'msif': 0.35, 'ple': 0.65}
        """
        
        # Extract context with defaults
        hour = context.get('hour_of_day', 12)
        endpoint_type = context.get('endpoint_type', 'api')
        traffic_level = context.get('traffic_level', 'medium')
        
        # ============= STEP 1: Base weights from time of day =============
        # During business hours (9am-5pm): Trust PLE more (better for APIs)
        # During off-hours: Trust MSIF more (better at night anomalies)
        if 9 <= hour <= 17:
            base_weights = config.THRESHOLDS.WEIGHT_RULES['peak_hours']
        else:
            base_weights = config.THRESHOLDS.WEIGHT_RULES['off_hours']
        
        # ============= STEP 2: Endpoint type adjustment =============
        # CPU-intensive endpoints: Trust MSIF more (better pattern detection)
        # API endpoints: Trust PLE more (better for API-specific anomalies)
        if endpoint_type == 'cpu_intensive':
            endpoint_adj = config.THRESHOLDS.WEIGHT_RULES['cpu_endpoint']
        else:
            endpoint_adj = config.THRESHOLDS.WEIGHT_RULES['api_endpoint']
        
        # ============= STEP 3: Traffic level adjustment =============
        # High traffic (>1000 req/min): Trust PLE more (more data)
        # Low traffic (<100 req/min): Balanced weights
        if traffic_level == 'high':
            traffic_adj = config.THRESHOLDS.WEIGHT_RULES['high_traffic']
        else:
            traffic_adj = config.THRESHOLDS.WEIGHT_RULES['low_traffic']
        
        # ============= STEP 4: Blend weights =============
        # 50% base + 25% endpoint + 25% traffic = 100%
        final_msif = (
            0.5 * base_weights['msif'] +
            0.25 * endpoint_adj['msif'] +
            0.25 * traffic_adj['msif']
        )
        final_ple = 1.0 - final_msif
        
        logger.debug(
            f"Dynamic weights: MSIF={final_msif:.2f}, PLE={final_ple:.2f} "
            f"(hour={hour}, endpoint={endpoint_type}, traffic={traffic_level})"
        )
        
        return {'msif': final_msif, 'ple': final_ple}
    
    # ============= PREDICTION FUSION =============
    
    def _fuse_predictions(self,
                         msif_score: float,
                         ple_score: float,
                         weights: Dict[str, float]) -> tuple:
        """
        Fuse predictions using confidence-based strategy
        
        Three strategies based on model agreement:
        1. High agreement (>85%): Use weighted average (models agree)
        2. Moderate agreement (60-85%): Use conservative max (some disagreement)
        3. Low agreement (<60%): Use max with warning (strong disagreement)
        
        Args:
            msif_score: MSIF-LSTM score [0-1]
            ple_score: PLE-GRU score [0-1]
            weights: {'msif': float, 'ple': float}
        
        Returns:
            (hybrid_score, fusion_method)
        """
        
        # Calculate model agreement
        confidence = 1.0 - abs(msif_score - ple_score)
        
        # ============= STRATEGY 1: High Agreement =============
        # Models mostly agree - use weighted average
        if confidence > config.THRESHOLDS.HIGH_AGREEMENT:
            hybrid_score = (
                weights['msif'] * msif_score +
                weights['ple'] * ple_score
            )
            fusion_method = 'weighted_agreement'
        
        # ============= STRATEGY 2: Moderate Agreement =============
        # Models somewhat disagree - be conservative
        # Use 95% of max (slightly biased toward one model)
        elif confidence > config.THRESHOLDS.MODERATE_AGREEMENT:
            hybrid_score = max(msif_score, ple_score) * 0.95
            fusion_method = 'conservative_max'
        
        # ============= STRATEGY 3: Low Agreement =============
        # Models strongly disagree - use max (fail-safe to higher score)
        # Log warning for investigation
        else:
            hybrid_score = max(msif_score, ple_score)
            fusion_method = 'conflict_detected'
            logger.warning(
                f"⚠️  Model disagreement detected: MSIF={msif_score:.3f}, "
                f"PLE={ple_score:.3f}. Using max score as fail-safe."
            )
        
        # Ensure score in valid range
        hybrid_score = np.clip(hybrid_score, 0.0, 1.0)
        
        return hybrid_score, fusion_method
    
    # ============= STATISTICS & MONITORING =============
    
    def get_stats(self) -> Dict:
        """
        Get detector statistics
        
        Returns:
            Dict with:
            - total_predictions: Total predictions made
            - anomalies_detected: Total anomalies detected
            - anomaly_rate: Percentage of predictions that were anomalies
            - models_loaded: Whether models are ready
            - msif_status: 'trained' or 'untrained'
            - ple_status: 'trained' or 'untrained'
        
        Example:
            >>> stats = detector.get_stats()
            >>> print(f"Anomaly rate: {stats['anomaly_rate']:.2%}")
        """
        return {
            'total_predictions': self.prediction_count,
            'anomalies_detected': self.anomaly_count,
            'anomaly_rate': (
                self.anomaly_count / max(self.prediction_count, 1)
            ),
            'models_loaded': self.models_loaded,
            'msif_status': 'trained' if self.msif.is_trained else 'untrained',
            'ple_status': 'trained' if self.ple.is_trained else 'untrained'
        }
    
    def reset_stats(self) -> None:
        """Reset prediction statistics"""
        self.prediction_count = 0
        self.anomaly_count = 0
        logger.info("✅ Statistics reset")
