-- V1: Enterprise Schema Baseline
-- Tables: api_logs, anomaly_detections, system_metrics, distributed_traces, alert_rules

-- ==================== api_logs ====================
CREATE TABLE IF NOT EXISTS api_logs (
  id BIGSERIAL PRIMARY KEY,
  endpoint VARCHAR(500) NOT NULL,
  http_method VARCHAR(10) NOT NULL,
  status_code INTEGER NOT NULL,
  response_time_ms BIGINT NOT NULL,
  request_size_bytes BIGINT,
  response_size_bytes BIGINT,
  cpu_usage_percent DOUBLE PRECISION,
  memory_usage_percent DOUBLE PRECISION,
  disk_io_bytes BIGINT,
  network_io_bytes BIGINT,
  error_rate DOUBLE PRECISION DEFAULT 0.0,
  error_count INTEGER DEFAULT 0,
  error_message TEXT,
  stack_trace TEXT,
  request_count INTEGER DEFAULT 1,
  user_id VARCHAR(255),
  ip_address INET,
  user_agent TEXT,
  request_body JSONB,
  response_body JSONB,
  request_headers JSONB,
  response_headers JSONB,
  trace_id VARCHAR(255),
  span_id VARCHAR(255),
  parent_span_id VARCHAR(255),
  service_name VARCHAR(255) NOT NULL,
  service_version VARCHAR(50),
  environment VARCHAR(50) DEFAULT 'production',
  hour_of_day INTEGER,
  day_of_week INTEGER,
  is_weekend BOOLEAN,
  is_business_hours BOOLEAN,
  is_processed BOOLEAN NOT NULL DEFAULT FALSE,
  processed_at TIMESTAMP,
  anomaly_detection_id BIGINT,
  ml_service_version VARCHAR(50),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255),
  metadata JSONB
);

CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_status_code ON api_logs(status_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_trace_id ON api_logs(trace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_unprocessed ON api_logs(is_processed, created_at) WHERE deleted_at IS NULL AND is_processed = FALSE;

-- ==================== anomaly_detections ====================
CREATE TABLE IF NOT EXISTS anomaly_detections (
  id BIGSERIAL PRIMARY KEY,
  api_log_id BIGINT,
  endpoint VARCHAR(500) NOT NULL,
  http_method VARCHAR(10) NOT NULL,
  msif_lstm_score DOUBLE PRECISION NOT NULL,
  ple_gru_score DOUBLE PRECISION NOT NULL,
  hybrid_ensemble_score DOUBLE PRECISION NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  severity_level VARCHAR(50) NOT NULL,
  anomaly_type VARCHAR(100),
  fusion_method VARCHAR(100) NOT NULL,
  ml_model_version VARCHAR(50),
  ml_processing_time_ms BIGINT,
  status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  is_acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by VARCHAR(255),
  acknowledged_at TIMESTAMP,
  acknowledgement_note TEXT,
  is_resolved BOOLEAN DEFAULT FALSE,
  resolved_by VARCHAR(255),
  resolved_at TIMESTAMP,
  resolution_note TEXT,
  is_false_positive BOOLEAN DEFAULT FALSE,
  marked_false_positive_by VARCHAR(255),
  marked_false_positive_at TIMESTAMP,
  trace_id VARCHAR(255),
  service_name VARCHAR(255),
  environment VARCHAR(50),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255),
  additional_context JSONB
);

CREATE INDEX idx_anomaly_detections_severity ON anomaly_detections(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_status ON anomaly_detections(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_created_at ON anomaly_detections(created_at DESC) WHERE deleted_at IS NULL;

-- ==================== system_metrics ====================
CREATE TABLE IF NOT EXISTS system_metrics (
  id BIGSERIAL PRIMARY KEY,
  api_log_id BIGINT,
  service_name VARCHAR(255) NOT NULL,
  endpoint VARCHAR(500),
  cpu_usage_percent DOUBLE PRECISION,
  memory_usage_percent DOUBLE PRECISION,
  disk_io_bytes BIGINT,
  network_io_bytes BIGINT,
  response_time_ms BIGINT,
  request_count INTEGER,
  error_rate DOUBLE PRECISION,
  metric_timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_metrics_timestamp ON system_metrics(metric_timestamp DESC);

-- ==================== distributed_traces ====================
CREATE TABLE IF NOT EXISTS distributed_traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL,           -- WITH underscore
    span_id VARCHAR(255) NOT NULL,            -- WITH underscore
    parent_span_id VARCHAR(255),              -- WITH underscore
    service_name VARCHAR(255) NOT NULL,       -- WITH underscore
    operation_name VARCHAR(255),              -- WITH underscore
    start_time TIMESTAMP NOT NULL,            -- WITH underscore
    duration_ms BIGINT NOT NULL,              -- WITH underscore
    status_code INTEGER,                      -- WITH underscore
    is_error BOOLEAN DEFAULT FALSE,           -- WITH underscore
    error_message TEXT,                       -- WITH underscore
    tags JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP  -- WITH underscore
);

CREATE INDEX idx_distributed_traces_trace_id ON distributed_traces(trace_id);

-- ==================== alert_rules ====================
CREATE TABLE IF NOT EXISTS alert_rules (
  id BIGSERIAL PRIMARY KEY,
  alert_name VARCHAR(255) NOT NULL,
  alert_description TEXT,
  condition_type VARCHAR(100) NOT NULL,
  condition_expression TEXT NOT NULL,
  threshold_value DOUBLE PRECISION,
  severity_level VARCHAR(50) NOT NULL,
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  notification_channels JSONB,
  notification_recipients JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255)
);

CREATE INDEX idx_alert_rules_enabled ON alert_rules(is_enabled) WHERE deleted_at IS NULL AND is_enabled = TRUE;

-- ==================== Views ====================
CREATE OR REPLACE VIEW v_recent_anomalies AS
SELECT
  a.id,
  a.endpoint,
  a.http_method,
  a.severity_level,
  a.hybrid_ensemble_score,
  a.status,
  a.is_acknowledged,
  a.created_at
FROM anomaly_detections a
WHERE a.deleted_at IS NULL
ORDER BY a.created_at DESC
LIMIT 100;
