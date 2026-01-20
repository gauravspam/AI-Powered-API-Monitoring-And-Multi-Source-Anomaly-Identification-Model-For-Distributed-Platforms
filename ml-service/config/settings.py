import os
from enum import Enum
from typing import Dict

# Compute paths at module level
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.getenv('LOG_PATH', os.path.join(_BASE_DIR, 'logs'))
_MODEL_DIR = os.getenv('MODEL_PATH', os.path.join(_BASE_DIR, 'trained_models'))

# Create directories
os.makedirs(_MODEL_DIR, exist_ok=True)
os.makedirs(_LOG_DIR, exist_ok=True)

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Config:
    """Base configuration - Single source of truth for all settings"""

    # ============= ENVIRONMENT =============
    ENV = os.getenv('ENVIRONMENT', 'development')
    DEBUG = ENV != 'production'

    # ============= PATHS =============
    BASE_DIR = _BASE_DIR
    MODEL_DIR = _MODEL_DIR
    LOG_DIR = _LOG_DIR

    # Create directories if not exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Aliases for API compatibility
    TRAINED_MODELS_PATH = MODEL_DIR
    MODEL_REGISTRY_PATH = os.path.join(MODEL_DIR, 'registry.json')
    API_VERSION = '1.0.0'
    API_PORT = 9000

    # ============= ML MODEL CONFIGURATION =============
    class ML_CONFIG:
        """Neural network architecture & training hyperparameters"""

        # Input shape (must match feature count from DataPreprocessor)
        FEATURE_COUNT = 10
        LOOKBACK_WINDOW = 1

        # MSIF-LSTM architecture (units per layer)
        MSIF_UNITS = [128, 64, 32, 16, 1]

        # PLE-GRU architecture (units per layer)
        PLE_UNITS = [128, 64, 32, 16, 1]

        # Training specifics
        DROPOUT_RATE = 0.2
        LEARNING_RATE = 0.001
        BATCH_SIZE = 32
        EPOCHS = 30
        VALIDATION_SPLIT = 0.2

        # Model ensemble weights (used if not context-aware)
        MSIF_WEIGHT = 0.6
        PLE_WEIGHT = 0.4

    # ============= FEATURE CONFIGURATION =============
    class FEATURES:
        """Feature definitions and validation bounds"""

        # Exact feature names in order (must match DataPreprocessor)
        NAMES = [
            'response_time',     # milliseconds (0-10000)
            'status_code',       # HTTP status (100-599)
            'request_count',     # requests per minute (0-100000)
            'error_rate',        # fraction 0-1 (0-1)
            'cpu_usage',         # percentage (0-100)
            'memory_usage',      # percentage (0-100)
            'network_io',        # MB/s (0-10000)
            'disk_io',           # MB/s (0-10000)
            'hour_of_day',       # 0-23
            'day_of_week'        # 0-6 (Mon=0, Sun=6)
        ]

        # Validation bounds (min, max) for each feature
        # Features outside these bounds are rejected
        BOUNDS = {
            'response_time': (0, 10000),        # 0-10 seconds
            'status_code': (100, 599),          # Valid HTTP codes
            'request_count': (0, 100000),       # 0-100k req/min
            'error_rate': (0, 1),               # 0-100%
            'cpu_usage': (0, 100),              # 0-100%
            'memory_usage': (0, 100),           # 0-100%
            'network_io': (0, 10000),           # 0-10k MB/s
            'disk_io': (0, 10000),              # 0-10k MB/s
            'hour_of_day': (0, 23),             # 0-23 hours
            'day_of_week': (0, 6)               # 0-6 days
        }

    # ============= THRESHOLD CONFIGURATION =============
    class THRESHOLDS:
        """Severity levels and context-aware weight rules"""

        # Anomaly score → Severity mapping
        # If score < 0.3: LOW
        # If 0.3 <= score < 0.5: MEDIUM
        # If 0.5 <= score < 0.7: HIGH
        # If score >= 0.7: CRITICAL
        SEVERITY_LEVELS = {
            'LOW': 0.3,
            'MEDIUM': 0.5,
            'HIGH': 0.7,
            'CRITICAL': 0.85
        }

        # Context-aware weight rules for hybrid ensemble
        # Format: {'msif': weight, 'ple': weight} (must sum to ~1.0)
        WEIGHT_RULES = {
            # Peak hours (9am-5pm): Trust PLE more (has better API detection)
            'peak_hours': {'msif': 0.35, 'ple': 0.65},

            # Off hours: Trust MSIF more (better at night anomalies)
            'off_hours': {'msif': 0.55, 'ple': 0.45},

            # CPU-intensive endpoints: Trust MSIF more
            'cpu_endpoint': {'msif': 0.60, 'ple': 0.40},

            # API endpoints: Trust PLE more
            'api_endpoint': {'msif': 0.40, 'ple': 0.60},

            # High traffic (>1000 req/min): Trust PLE more
            'high_traffic': {'msif': 0.35, 'ple': 0.65},

            # Low traffic (<100 req/min): Balanced
            'low_traffic': {'msif': 0.50, 'ple': 0.50}
        }

        # Model agreement thresholds for fusion strategy
        HIGH_AGREEMENT = 0.85      # If models agree >85%, use weighted avg
        MODERATE_AGREEMENT = 0.60  # If models agree 60-85%, use conservative max

    # ============= MONITORING CONFIGURATION =============
    class MONITORING:
        """Model performance monitoring and drift detection"""


        # Enable metrics collection
        ENABLE_METRICS = True
        ENABLE_PROFILING = os.getenv('ENVIRONMENT', 'development') == 'development'

        # Statistical drift detection
        DRIFT_WINDOW_SIZE = 1000      # Check every 1000 predictions
        DRIFT_THRESHOLD = 0.05        # Flag if >5% statistical difference

        # Performance alerts
        LATENCY_WARNING_MS = 100      # Warn if prediction takes >100ms
        LATENCY_CRITICAL_MS = 500     # Critical if >500ms

    # ============= LOGGING CONFIGURATION =============
    class LOGGING:
        """Structured logging setup"""

        # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        LEVEL = os.getenv('LOG_LEVEL', 'INFO')

        # Format string
        FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # Log file path - use os.getenv directly instead of LOG_DIR
        FILE = os.path.join(_LOG_DIR, 'ml-service.log')

        # Rotating file handler limits
        MAX_BYTES = 10485760        # 10MB per file
        BACKUP_COUNT = 5            # Keep 5 backup files

    # ============= API CONFIGURATION =============
    class API:
        """Flask API configuration"""

        HOST = os.getenv('API_HOST', '0.0.0.0')
        PORT = int(os.getenv('API_PORT', 9000))
        WORKERS = int(os.getenv('API_WORKERS', 4))
        TIMEOUT = 60

    # ============= UTILITY METHODS =============

    @classmethod
    def get_severity(cls, score: float) -> str:
        """
        Map anomaly score (0-1) to severity level

        Args:
            score: Anomaly score between 0 and 1

        Returns:
            Severity string: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
        """
        thresholds = cls.THRESHOLDS.SEVERITY_LEVELS

        if score < thresholds['LOW']:
            return 'LOW'
        elif score < thresholds['MEDIUM']:
            return 'MEDIUM'
        elif score < thresholds['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'

    @classmethod
    def validate_features(cls, features: Dict[str, float]) -> bool:
        """
        Quick validation that features are within bounds

        Args:
            features: Dict with feature values

        Returns:
            True if all present features are within bounds
        """
        for feature_name, bounds in cls.FEATURES.BOUNDS.items():
            if feature_name in features:
                value = features[feature_name]
                if not (bounds[0] <= value <= bounds[1]):
                    return False
        return True

# Export single config instance for app-wide use
config = Config()
