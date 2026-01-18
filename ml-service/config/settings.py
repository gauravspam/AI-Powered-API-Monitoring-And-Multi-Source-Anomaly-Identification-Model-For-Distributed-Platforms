"""Configuration settings for ML service"""
import os
from pathlib import Path

class Config:
    """Base configuration"""
    
    # Service
    SERVICE_NAME = "api-monitoring-ml-service"
    VERSION = "1.0.0"
    HOST = os.getenv("ML_SERVICE_HOST", "0.0.0.0")
    PORT = int(os.getenv("ML_SERVICE_PORT", 9000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Model paths
    BASE_DIR = Path(__file__).parent.parent
    MODELS_DIR = BASE_DIR / "models" / "saved"
    MSIF_MODEL_PATH = MODELS_DIR / "msif_lstm_model.h5"
    PLE_MODEL_PATH = MODELS_DIR / "ple_gru_model.h5"
    
    # MSIF-LSTM Configuration
    MSIF_WINDOW_SIZE = 60  # 60 minutes
    MSIF_FEATURES = 5  # cpu, memory, response_time, error_rate, request_count
    MSIF_LSTM_UNITS = 128
    MSIF_DROPOUT = 0.3
    
    # PLE-GRU Configuration
    PLE_WINDOW_SIZE = 1440  # 24 hours
    PLE_FEATURES = 7  # Additional derived features
    PLE_GRU_UNITS = 256
    PLE_DROPOUT = 0.4
    
    # Hybrid Fusion
    MSIF_WEIGHT = 0.6
    PLE_WEIGHT = 0.4
    FUSION_THRESHOLD = 0.7
    
    # Anomaly Thresholds
    CRITICAL_THRESHOLD = 0.9
    HIGH_THRESHOLD = 0.7
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.3
    
    @classmethod
    def get_severity(cls, score: float) -> str:
        """Map anomaly score to severity level"""
        if score >= cls.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif score >= cls.HIGH_THRESHOLD:
            return "HIGH"
        elif score >= cls.MEDIUM_THRESHOLD:
            return "MEDIUM"
        elif score >= cls.LOW_THRESHOLD:
            return "LOW"
        return "NORMAL"
    
    @classmethod
    def get_confidence(cls, score: float, variance: float = 0.1) -> str:
        """Calculate confidence level"""
        if variance < 0.1 and abs(score - 0.5) > 0.3:
            return "HIGH"
        elif variance < 0.2:
            return "MEDIUM"
        return "LOW"

config = Config()
