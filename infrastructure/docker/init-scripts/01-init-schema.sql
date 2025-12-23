-- PostgreSQL Initialization Script for API Monitoring Platform
-- This script creates the initial database schema

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for storing ML model configurations
CREATE TABLE IF NOT EXISTS model_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL, -- 'MSFI-LSTM' or 'PLE-GRU'
    model_path VARCHAR(500),
    version VARCHAR(50),
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing pipeline settings
CREATE TABLE IF NOT EXISTS pipeline_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(255) NOT NULL UNIQUE,
    setting_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing alert rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    condition_type VARCHAR(50) NOT NULL, -- 'threshold', 'anomaly_score', 'pattern'
    condition_config JSONB NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    is_enabled BOOLEAN DEFAULT true,
    notification_channels JSONB, -- Array of channel configs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing anomaly scores from ML models
CREATE TABLE IF NOT EXISTS anomaly_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_id VARCHAR(255),
    service VARCHAR(255),
    model_name VARCHAR(255) NOT NULL,
    score DECIMAL(10, 6) NOT NULL,
    threshold DECIMAL(10, 6) DEFAULT 0.7,
    is_anomaly BOOLEAN DEFAULT false,
    log_data JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_name) REFERENCES model_configs(model_name)
);

-- Table for storing alert history
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_rule_id UUID NOT NULL,
    anomaly_score_id UUID,
    status VARCHAR(50) NOT NULL, -- 'triggered', 'resolved', 'acknowledged'
    message TEXT,
    notification_sent BOOLEAN DEFAULT false,
    notification_channels JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (alert_rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (anomaly_score_id) REFERENCES anomaly_scores(id)
);

-- Table for log metadata (used by Fluentd)
CREATE TABLE IF NOT EXISTS log_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(255),
    level VARCHAR(50),
    message TEXT,
    timestamp BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_anomaly_scores_service ON anomaly_scores(service);
CREATE INDEX IF NOT EXISTS idx_anomaly_scores_detected_at ON anomaly_scores(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_scores_is_anomaly ON anomaly_scores(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert_rule_id ON alert_history(alert_rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON alert_history(status);
CREATE INDEX IF NOT EXISTS idx_alert_history_created_at ON alert_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_log_metadata_service ON log_metadata(service);
CREATE INDEX IF NOT EXISTS idx_log_metadata_timestamp ON log_metadata(timestamp DESC);

-- Insert default model configurations
INSERT INTO model_configs (model_name, model_type, version, parameters, is_active)
VALUES 
    ('msfi-lstm-v1', 'MSFI-LSTM', '1.0.0', '{"sequence_length": 100, "batch_size": 32, "threshold": 0.7}'::jsonb, true),
    ('ple-gru-v1', 'PLE-GRU', '1.0.0', '{"sequence_length": 100, "batch_size": 32, "threshold": 0.75}'::jsonb, true)
ON CONFLICT (model_name) DO NOTHING;

-- Insert default pipeline settings
INSERT INTO pipeline_settings (setting_key, setting_value, description)
VALUES 
    ('log_retention_days', '30', 'Number of days to retain logs in OpenSearch'),
    ('anomaly_detection_interval_seconds', '60', 'Interval in seconds to run anomaly detection'),
    ('batch_size', '100', 'Number of logs to process in each batch'),
    ('max_anomaly_score_history', '10000', 'Maximum number of anomaly scores to keep in database')
ON CONFLICT (setting_key) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_model_configs_updated_at BEFORE UPDATE ON model_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_settings_updated_at BEFORE UPDATE ON pipeline_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

