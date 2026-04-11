# ML Service Configuration
# Batch processing and model settings

# Batch Processing Settings
BATCH_SIZE_LOGS = 5000
BATCH_SIZE_TRACES = 5000
BATCH_SIZE_METRICS = 5000
BATCH_INTERVAL_SECONDS = 120  # 2 minutes

# Model Settings
MSIF_WEIGHT = 0.6
PLE_WEIGHT = 0.4
FUSION_THRESHOLD = 0.7

# Severity Thresholds
CRITICAL_THRESHOLD = 0.8
HIGH_THRESHOLD = 0.6
MEDIUM_THRESHOLD = 0.4
LOW_THRESHOLD = 0.0

# OpenSearch Configuration
OPENSEARCH_HOST = localhost
OPENSEARCH_PORT = 9200
OPENSEARCH_SCHEME = http

# Index Names
INDEX_LOGS = logs
INDEX_METRICS = metrics
INDEX_TRACES = traces
INDEX_ANOMALIES = anomalies

# Model Configuration
MODEL_EMBEDDING_DIM = 128
MSIF_LSTM_HIDDEN_DIM = 64
PLE_GRU_HIDDEN_DIM = 64
NUM_EXPERTS = 3

# Hardware Recommendations (for batch size optimization)
# CPU Only: 2500-5000 per modality
# GPU 4GB: 5000-10000 per modality
# GPU 16GB+: 10000-50000 per modality