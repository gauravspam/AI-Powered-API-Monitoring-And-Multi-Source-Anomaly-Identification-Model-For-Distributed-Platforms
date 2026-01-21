-- Flyway Migration V6: Add ML processing tracking to api_logs table
-- These fields track which logs have been analyzed and link to results

-- Add processing status flag
ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS processed BOOLEAN NOT NULL DEFAULT FALSE;

-- Add processing timestamp
ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- Add foreign key to anomaly_scores
ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS anomaly_id BIGINT;

-- Add ML version tracking
ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS ml_service_version VARCHAR(50);

-- Add foreign key constraint
ALTER TABLE api_logs
    ADD CONSTRAINT fk_api_logs_anomaly_id
    FOREIGN KEY (anomaly_id)
    REFERENCES anomaly_scores(id)
    ON DELETE SET NULL;

-- Performance indexes for finding unprocessed logs
CREATE INDEX idx_api_logs_processed_created_at ON api_logs(processed, created_at DESC);
CREATE INDEX idx_api_logs_anomaly_id ON api_logs(anomaly_id);
CREATE INDEX idx_api_logs_processed_false ON api_logs(processed) WHERE processed = FALSE;

-- Comments
COMMENT ON COLUMN api_logs.processed IS 'Whether this log has been analyzed by ML service';
COMMENT ON COLUMN api_logs.processed_at IS 'Timestamp when ML analysis completed';
COMMENT ON COLUMN api_logs.anomaly_id IS 'Foreign key to anomaly_scores if anomaly detected';
COMMENT ON COLUMN api_logs.ml_service_version IS 'Version of ML service that processed this log';
