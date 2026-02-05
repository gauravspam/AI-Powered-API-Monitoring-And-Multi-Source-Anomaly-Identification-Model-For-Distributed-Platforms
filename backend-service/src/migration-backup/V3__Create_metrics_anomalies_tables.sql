CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    api_id BIGINT NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time DOUBLE PRECISION,
    request_size BIGINT,
    response_size BIGINT,
    cpu_usage DOUBLE PRECISION,
    memory_usage DOUBLE PRECISION,
    error_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_api_id ON metrics(api_id);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_created_at ON metrics(created_at);

CREATE TABLE IF NOT EXISTS anomalies (
    id BIGSERIAL PRIMARY KEY,
    api_name VARCHAR(255) NOT NULL,
    msif_lstm_score DOUBLE PRECISION,
    ple_gru_score DOUBLE PRECISION,
    hybrid_score DOUBLE PRECISION,
    final_anomaly_score DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    severity VARCHAR(20),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    ml_model_used VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_api_name ON anomalies(api_name);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
