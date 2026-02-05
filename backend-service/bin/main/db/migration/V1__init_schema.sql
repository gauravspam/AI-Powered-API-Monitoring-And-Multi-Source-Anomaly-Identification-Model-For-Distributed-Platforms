-- V1: Enterprise Schema Baseline (snake_case + proper naming)
-- Tables: api_logs, anomaly_detections, system_metrics, distributed_traces, alert_rules

-- ==================== api_logs ====================
CREATE TABLE IF NOT EXISTS api_logs (
  id BIGSERIAL PRIMARY KEY,
  
  -- API Request Info
  endpoint VARCHAR(500) NOT NULL,
  http_method VARCHAR(10) NOT NULL,
  status_code INTEGER NOT NULL,
  response_time_ms BIGINT NOT NULL,
  
  -- Request/Response Size
  request_size_bytes BIGINT,
  response_size_bytes BIGINT,
  
  -- System Metrics
  cpu_usage_percent DOUBLE PRECISION,
  memory_usage_percent DOUBLE PRECISION,
  disk_io_bytes BIGINT,
  network_io_bytes BIGINT,
  
  -- Error Tracking
  error_rate DOUBLE PRECISION DEFAULT 0.0,
  error_count INTEGER DEFAULT 0,
  error_message TEXT,
  stack_trace TEXT,
  
  -- Request Context
  request_count INTEGER DEFAULT 1,
  user_id VARCHAR(255),
  ip_address INET,
  user_agent TEXT,
  
  -- Request/Response Bodies (JSON)
  request_body JSONB,
  response_body JSONB,
  request_headers JSONB,
  response_headers JSONB,
  
  -- Distributed Tracing
  trace_id VARCHAR(255),
  span_id VARCHAR(255),
  parent_span_id VARCHAR(255),
  
  -- Service Context
  service_name VARCHAR(255) NOT NULL,
  service_version VARCHAR(50),
  environment VARCHAR(50) DEFAULT 'production',
  
  -- Temporal Features (for ML)
  hour_of_day INTEGER,
  day_of_week INTEGER,
  is_weekend BOOLEAN,
  is_business_hours BOOLEAN,
  
  -- Processing Status
  is_processed BOOLEAN NOT NULL DEFAULT FALSE,
  processed_at TIMESTAMP,
  anomaly_detection_id BIGINT,
  ml_service_version VARCHAR(50),
  
  -- Audit Fields
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255),
  
  -- Metadata
  metadata JSONB
);

-- Indexes for api_logs
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_status_code ON api_logs(status_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_trace_id ON api_logs(trace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_endpoint_created ON api_logs(endpoint, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_service_created ON api_logs(service_name, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_unprocessed ON api_logs(is_processed, created_at) WHERE deleted_at IS NULL AND is_processed = FALSE;

-- ==================== anomaly_detections ====================
CREATE TABLE IF NOT EXISTS anomaly_detections (
  id BIGSERIAL PRIMARY KEY,
  
  -- Link to source log
  api_log_id BIGINT,
  
  -- API Info (denormalized)
  endpoint VARCHAR(500) NOT NULL,
  http_method VARCHAR(10) NOT NULL,
  
  -- ML Model Scores (all three algorithms)
  msif_lstm_score DOUBLE PRECISION NOT NULL,
  ple_gru_score DOUBLE PRECISION NOT NULL,
  hybrid_ensemble_score DOUBLE PRECISION NOT NULL,
  
  -- Confidence & Severity
  confidence_score DOUBLE PRECISION NOT NULL,
  severity_level VARCHAR(50) NOT NULL,
  anomaly_type VARCHAR(100),
  
  -- ML Model Info
  fusion_method VARCHAR(100) NOT NULL,
  ml_model_version VARCHAR(50),
  ml_processing_time_ms BIGINT,
  
  -- Status Management
  status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  is_acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_by VARCHAR(255),
  acknowledged_at TIMESTAMP,
  acknowledgement_note TEXT,
  
  -- Resolution
  is_resolved BOOLEAN DEFAULT FALSE,
  resolved_by VARCHAR(255),
  resolved_at TIMESTAMP,
  resolution_note TEXT,
  
  -- False Positive Handling
  is_false_positive BOOLEAN DEFAULT FALSE,
  marked_false_positive_by VARCHAR(255),
  marked_false_positive_at TIMESTAMP,
  
  -- Distributed Tracing
  trace_id VARCHAR(255),
  
  -- Service Context
  service_name VARCHAR(255),
  environment VARCHAR(50),
  
  -- Audit Fields
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255),
  
  -- Metadata
  additional_context JSONB
);

-- Indexes for anomaly_detections
CREATE INDEX idx_anomaly_detections_endpoint ON anomaly_detections(endpoint) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_severity ON anomaly_detections(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_status ON anomaly_detections(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_created_at ON anomaly_detections(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_trace_id ON anomaly_detections(trace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_api_log_id ON anomaly_detections(api_log_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_severity_status ON anomaly_detections(severity_level, status, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_critical_unack ON anomaly_detections(created_at DESC) WHERE deleted_at IS NULL AND is_acknowledged = FALSE AND severity_level IN ('CRITICAL', 'HIGH');

-- ==================== system_metrics ====================
CREATE TABLE IF NOT EXISTS system_metrics (
  id BIGSERIAL PRIMARY KEY,
  
  -- Link to API log if available
  api_log_id BIGINT,
  
  -- Service Info
  service_name VARCHAR(255) NOT NULL,
  endpoint VARCHAR(500),
  
  -- Metrics
  cpu_usage_percent DOUBLE PRECISION,
  memory_usage_percent DOUBLE PRECISION,
  disk_io_bytes BIGINT,
  network_io_bytes BIGINT,
  response_time_ms BIGINT,
  request_count INTEGER,
  error_rate DOUBLE PRECISION,
  
  -- Timestamp
  metric_timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for system_metrics
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(metric_timestamp DESC);
CREATE INDEX idx_system_metrics_service ON system_metrics(service_name, metric_timestamp DESC);
CREATE INDEX idx_system_metrics_api_log_id ON system_metrics(api_log_id) WHERE api_log_id IS NOT NULL;

-- ==================== distributed_traces ====================
CREATE TABLE IF NOT EXISTS distributed_traces (
  id BIGSERIAL PRIMARY KEY,
  
  -- Trace Info
  trace_id VARCHAR(255) NOT NULL,
  span_id VARCHAR(255) NOT NULL,
  parent_span_id VARCHAR(255),
  
  -- Service Info
  service_name VARCHAR(255) NOT NULL,
  operation_name VARCHAR(255),
  
  -- Timing
  start_time TIMESTAMP NOT NULL,
  duration_ms BIGINT NOT NULL,
  
  -- Status
  status_code INTEGER,
  is_error BOOLEAN DEFAULT FALSE,
  error_message TEXT,
  
  -- Tags (flexible metadata)
  tags JSONB,
  
  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for distributed_traces
CREATE INDEX idx_distributed_traces_trace_id ON distributed_traces(trace_id);
CREATE INDEX idx_distributed_traces_service ON distributed_traces(service_name, start_time DESC);
CREATE INDEX idx_distributed_traces_parent ON distributed_traces(parent_span_id) WHERE parent_span_id IS NOT NULL;
CREATE INDEX idx_distributed_traces_created_at ON distributed_traces(created_at DESC);

-- ==================== alert_rules ====================
CREATE TABLE IF NOT EXISTS alert_rules (
  id BIGSERIAL PRIMARY KEY,
  
  -- Alert Config
  alert_name VARCHAR(255) NOT NULL,
  alert_description TEXT,
  
  -- Condition
  condition_type VARCHAR(100) NOT NULL,
  condition_expression TEXT NOT NULL,
  threshold_value DOUBLE PRECISION,
  
  -- Severity
  severity_level VARCHAR(50) NOT NULL,
  
  -- Status
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  
  -- Notification
  notification_channels JSONB,
  notification_recipients JSONB,
  
  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  deleted_at TIMESTAMP,
  deleted_by VARCHAR(255)
);

-- Indexes for alert_rules
CREATE INDEX idx_alert_rules_enabled ON alert_rules(is_enabled) WHERE deleted_at IS NULL AND is_enabled = TRUE;
CREATE INDEX idx_alert_rules_severity ON alert_rules(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_alert_rules_created_at ON alert_rules(created_at DESC) WHERE deleted_at IS NULL;

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

-- ==================== Comments ====================
COMMENT ON TABLE api_logs IS 'Primary data source: Stores API request/response data for ML-based anomaly detection';
COMMENT ON TABLE anomaly_detections IS 'ML anomaly detection results: MSIF-LSTM, PLE-GRU, and Hybrid-Ensemble models';
COMMENT ON TABLE system_metrics IS 'Time-series system metrics: CPU, memory, disk, network';
COMMENT ON TABLE distributed_traces IS 'Distributed tracing data for request correlation';
COMMENT ON TABLE alert_rules IS 'Alert rules: configuration, thresholds, notification channels';
