"""
Hybrid Anomaly Detector (Lightweight version without numpy)
"""
import logging
from config.settings import config

logger = logging.getLogger(__name__)

class HybridAnomalyDetector:
    """Hybrid detector - placeholder mode"""
    
    def __init__(self):
        self.msif_weight = config.MSIF_WEIGHT
        self.ple_weight = config.PLE_WEIGHT
        logger.info("HybridAnomalyDetector initialized (lightweight mode)")
    
    def predict(self, msif_features=None, ple_features=None, method='AGGREGATE'):
        """Predict anomaly scores"""
        
        # Simple placeholder calculation
        msif_score = 0.45 if msif_features else 0.0
        ple_score = 0.35 if ple_features else 0.0
        
        # Hybrid fusion
        if method == 'MSIF_ONLY':
            hybrid_score = msif_score
        elif method == 'PLE_ONLY':
            hybrid_score = ple_score
        else:  # AGGREGATE
            hybrid_score = (self.msif_weight * msif_score + 
                           self.ple_weight * ple_score)
        
        severity = config.get_severity(hybrid_score)
        confidence = config.get_confidence(hybrid_score)
        
        return {
            'msif_score': float(msif_score),
            'ple_score': float(ple_score),
            'hybrid_score': float(hybrid_score),
            'severity': severity,
            'confidence': confidence
        }
