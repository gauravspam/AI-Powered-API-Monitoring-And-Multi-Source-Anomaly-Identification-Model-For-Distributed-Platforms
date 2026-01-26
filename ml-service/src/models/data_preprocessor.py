"""
Production-grade data preprocessing pipeline

Responsibilities:
1. Extract features from raw API logs
2. Validate data quality against bounds
3. Normalize features using fitted StandardScaler
4. Handle missing/invalid values
5. Persist scaler for inference consistency

Critical: Scaler must be FITTED on training data before normalization
"""

import numpy as np
import pickle
import os
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
from src.logger import logger
from config.settings import config

class DataPreprocessor:
    """
    Production-grade data preprocessing with scaler persistence
    
    Workflow:
    1. Training phase: fit(X_train) → save()
    2. Inference phase: load() → extract_features() → normalize_features()
    
    Key attributes:
    - scaler: sklearn StandardScaler (scales features to mean=0, std=1)
    - feature_names: List of 10 feature names
    - is_fitted: Boolean flag (must be True before normalize)
    - feature_stats: Dict with mean/std/min/max for monitoring
    """
    
    def __init__(self):
        """Initialize preprocessor (scaler NOT fitted yet)"""
        self.scaler = StandardScaler()
        self.feature_names = config.FEATURES.NAMES  # 10 feature names from config
        self.is_fitted = False
        self.feature_stats = None
        
        logger.info(
            f"DataPreprocessor initialized with {len(self.feature_names)} features: "
            f"{self.feature_names}"
        )
    
    # ============= FITTING PHASE (Training Only) =============
    
    def fit(self, data: np.ndarray) -> None:
        """
        Fit StandardScaler on training data
        
        MUST be called ONCE during training before any normalization
        Computes mean and std of each feature from training data
        
        Args:
            data: np.ndarray of shape (n_samples, 10)
                  Must have exactly 10 features matching config.FEATURES.NAMES
        
        Raises:
            ValueError if feature count doesn't match
        
        Example:
            >>> X_train = np.array([[200, 200, 100, ...], ...])  # shape: (8000, 10)
            >>> preprocessor = DataPreprocessor()
            >>> preprocessor.fit(X_train)
            >>> # Now preprocessor.is_fitted = True
        """
        
        # Validate shape
        if data.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, "
                f"got {data.shape[1]} in data"
            )
        
        # Fit scaler on training data
        # This computes mean and std for each feature
        self.scaler.fit(data)
        self.is_fitted = True
        
        # Store statistics for monitoring/debugging
        self.feature_stats = {
            'mean': self.scaler.mean_.tolist(),
            'std': self.scaler.scale_.tolist(),
            'min': data.min(axis=0).tolist(),
            'max': data.max(axis=0).tolist()
        }
        
        logger.info(f"✅ Scaler fitted on {len(data):,} training samples")
        logger.debug(f"Feature means: {self.feature_stats['mean']}")
        logger.debug(f"Feature stds: {self.feature_stats['std']}")
    
    def save(self, path: str) -> None:
        """
        Persist fitted scaler to disk
        
        Must call fit() BEFORE save()
        Saves two files:
        - scaler.pkl: The fitted StandardScaler object
        - scaler_stats.json: Statistics for monitoring
        
        Args:
            path: Directory path to save files
        
        Raises:
            RuntimeError if scaler not fitted yet
        
        Example:
            >>> preprocessor.fit(X_train)
            >>> preprocessor.save('./trained_models')
            >>> # Creates: trained_models/scaler.pkl
            >>> #         trained_models/scaler_stats.json
        """
        
        if not self.is_fitted:
            raise RuntimeError(
                "❌ Cannot save unfitted scaler! Call fit(X_train) first."
            )
        
        os.makedirs(path, exist_ok=True)
        
        # Save scaler as binary pickle
        scaler_path = os.path.join(path, 'scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save statistics as JSON (human-readable)
        import json
        stats_path = os.path.join(path, 'scaler_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(self.feature_stats, f, indent=2)
        
        logger.info(f"✅ Scaler saved to {scaler_path}")
        logger.info(f"✅ Statistics saved to {stats_path}")
    
    def load(self, path: str) -> None:
        """
        Load pre-fitted scaler from disk
        
        Call this during model inference/deployment
        Must be called BEFORE normalize_features()
        
        Args:
            path: Directory path where scaler files are saved
        
        Raises:
            FileNotFoundError if scaler.pkl not found
        
        Example:
            >>> preprocessor = DataPreprocessor()
            >>> preprocessor.load('./trained_models')
            >>> # Now ready to normalize
            >>> normalized = preprocessor.normalize_features(features)
        """
        
        scaler_path = os.path.join(path, 'scaler.pkl')
        stats_path = os.path.join(path, 'scaler_stats.json')
        
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(
                f"Scaler not found at {scaler_path}. "
                f"Make sure to save during training first."
            )
        
        # Load scaler
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # Load statistics if available
        if os.path.exists(stats_path):
            import json
            with open(stats_path, 'r') as f:
                self.feature_stats = json.load(f)
        
        self.is_fitted = True
        logger.info(f"✅ Scaler loaded from {scaler_path}")
    
    # ============= FEATURE EXTRACTION & NORMALIZATION =============
    
    def extract_features(self, log_entry: Dict) -> np.ndarray:
        """
        Extract 10 features from raw API log entry
        
        Reads values from dict in config.FEATURES.NAMES order
        Handles missing values (defaults to 0)
        Converts all to float
        
        Args:
            log_entry: Dict with API metrics
                Example: {
                    'response_time': 250,
                    'status_code': 200,
                    'request_count': 100,
                    ...
                }
        
        Returns:
            np.ndarray of shape (10,) with float values
        
        Example:
            >>> log = {
            ...     'response_time': 250,
            ...     'status_code': 200,
            ...     'request_count': 100,
            ...     'error_rate': 0.02,
            ...     'cpu_usage': 50,
            ...     'memory_usage': 60,
            ...     'network_io': 300,
            ...     'disk_io': 100,
            ...     'hour_of_day': 14,
            ...     'day_of_week': 1
            ... }
            >>> features = preprocessor.extract_features(log)
            >>> features
            array([250.,  200.,  100.,    0.02,  50.,  60., 300., 100.,  14.,   1.])
        """
        
        features = []
        
        for feature_name in self.feature_names:
            # Get value from dict (default to 0 if missing)
            value = log_entry.get(feature_name, 0)
            
            # Handle None
            if value is None:
                value = 0
                logger.warning(
                    f"Missing feature '{feature_name}', using 0 as default"
                )
            
            # Convert to float
            try:
                value = float(value)
            except (ValueError, TypeError):
                logger.warning(
                    f"Could not convert '{feature_name}'={value} to float, using 0"
                )
                value = 0.0
            
            features.append(value)
        
        return np.array(features, dtype=np.float32)
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features using fitted scaler
        
        Formula: (x - mean) / std for each feature
        
        REQUIRES: fit() or load() must be called first
        
        Args:
            features: np.ndarray of shape (10,) or (batch_size, 10)
        
        Returns:
            Normalized features with same shape
        
        Raises:
            RuntimeError if scaler not fitted
        
        Example:
            >>> features = np.array([250, 200, 100, 0.02, 50, 60, 300, 100, 14, 1])
            >>> normalized = preprocessor.normalize_features(features)
            >>> normalized
            array([ 0.05,  1.  ,  0.5 ,  0.01,  0.5 ,  0.6 ,  0.3 ,  0.1 ,  0.58,  0.14])
        """
        
        if not self.is_fitted:
            raise RuntimeError(
                "❌ Scaler not fitted! Call fit() with training data first, "
                "or load() to load pre-fitted scaler."
            )
        
        # Handle single sample vs batch
        if features.ndim == 1:
            features = features.reshape(1, -1)
            normalized = self.scaler.transform(features)[0]
        else:
            normalized = self.scaler.transform(features)
        
        return normalized
    
    # ============= VALIDATION =============
    
    def validate_features(self, log_entry: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate features are within acceptable bounds
        
        Uses config.FEATURES.BOUNDS to check each feature
        
        Args:
            log_entry: Dict with API metrics
        
        Returns:
            (is_valid: bool, error_message: Optional[str])
            If valid: (True, None)
            If invalid: (False, "error description")
        
        Example:
            >>> log = {'response_time': 250, ...}
            >>> is_valid, error = preprocessor.validate_features(log)
            >>> if not is_valid:
            ...     print(f"Validation failed: {error}")
        """
        
        for feature_name, bounds in config.FEATURES.BOUNDS.items():
            if feature_name not in log_entry:
                continue  # Skip if not present
            
            value = log_entry[feature_name]
            
            # Try to convert to float
            try:
                value = float(value)
            except (ValueError, TypeError):
                return False, f"Invalid type for {feature_name}: {value}"
            
            # Check bounds
            if not (bounds[0] <= value <= bounds[1]):
                return (
                    False,
                    f"{feature_name} out of bounds: {value} "
                    f"not in [{bounds[0]}, {bounds[1]}]"
                )
        
        return True, None
    
    # ============= BATCH PROCESSING =============
    
    def preprocess_batch(self, log_entries: List[Dict]) -> np.ndarray:
        """
        Process multiple log entries efficiently
        
        Validates each entry, extracts and normalizes features
        Skips invalid entries with warning
        
        Args:
            log_entries: List of dicts with API metrics
        
        Returns:
            np.ndarray of shape (valid_count, 10)
        
        Example:
            >>> logs = [
            ...     {'response_time': 250, ...},
            ...     {'response_time': 300, ...},
            ...     {'response_time': 350, ...}
            ... ]
            >>> batch = preprocessor.preprocess_batch(logs)
            >>> batch.shape
            (3, 10)
        """
        
        features_list = []
        
        for i, log_entry in enumerate(log_entries):
            # Validate
            is_valid, error_msg = self.validate_features(log_entry)
            if not is_valid:
                logger.warning(f"Skipping invalid log {i}: {error_msg}")
                continue
            
            # Extract features
            features = self.extract_features(log_entry)
            
            # Normalize
            normalized = self.normalize_features(features)
            features_list.append(normalized)
        
        return np.array(features_list, dtype=np.float32)
