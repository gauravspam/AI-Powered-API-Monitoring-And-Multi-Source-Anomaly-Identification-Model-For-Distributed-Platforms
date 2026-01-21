-- Flyway Migration V5: Create anomaly_scores table for ML predictions
-- This table stores all anomaly detection results from the ML service

CREATE TABLE IF NOT EXISTS anomaly_scores (
    id BIGSERIAL PRIMARY KEY,

    -- API Identification
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',

    -- ML Model Scores (3 scores from hybrid model)
    msif_lstm_score DOUBLE PRECISION,
    ple_gru_score DOUBLE PRECISION,
    hybrid_ensemble_score DOUBLE PRECISION NOT NULL,

    -- Analysis Metadata
    confidence DOUBLE PRECISION,
    severity VARCHAR(20) NOT NULL,
    fusion_method VARCHAR(50),

    -- Status Tracking
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,

    -- Diagnostics & Tracing
    trace_id VARCHAR(255),
    ml_processing_time_ms BIGINT,
    ml_service_version VARCHAR(50),

    -- Audit Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_anomaly_scores_endpoint_created_at ON anomaly_scores(endpoint, created_at DESC);
CREATE INDEX idx_anomaly_scores_severity_created_at ON anomaly_scores(severity, created_at DESC);
CREATE INDEX idx_anomaly_scores_status ON anomaly_scores(status);
CREATE INDEX idx_anomaly_scores_created_at ON anomaly_scores(created_at DESC);
CREATE INDEX idx_anomaly_scores_trace_id ON anomaly_scores(trace_id);
CREATE INDEX idx_anomaly_scores_hybrid_score ON anomaly_scores(hybrid_ensemble_score DESC);

-- Comments for documentation
COMMENT ON TABLE anomaly_scores IS 'Stores ML anomaly detection results from hybrid MSIF-LSTM + PLE-GRU models';
COMMENT ON COLUMN anomaly_scores.msif_lstm_score IS 'Multi-Scale Isolation Forest + LSTM score (short-term)';
COMMENT ON COLUMN anomaly_scores.ple_gru_score IS 'Probabilistic Label Enhancement + GRU score (long-term)';
COMMENT ON COLUMN anomaly_scores.hybrid_ensemble_score IS 'Weighted ensemble score combining MSIF and PLE';
COMMENT ON COLUMN anomaly_scores.severity IS 'Calculated severity: LOW, MEDIUM, HIGH, CRITICAL';
COMMENT ON COLUMN anomaly_scores.status IS 'Lifecycle status: ACTIVE, ACKNOWLEDGED, RESOLVED';
