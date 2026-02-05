-- ============================================================================
-- Priority 1: Enterprise-Grade Schema Migration
-- Strategy: Clean Slate (Drop old + Create new)
-- Tables: api_logs, anomaly_detections, system_metrics, distributed_traces, alert_rules
-- ============================================================================

-- ============================================================================
-- PART 1: Cleanup (Drop old tables if they exist)
-- ============================================================================

DROP TABLE IF EXISTS public.anomalies CASCADE;
DROP TABLE IF EXISTS public.metrics CASCADE;
DROP TABLE IF EXISTS public.traces CASCADE;
DROP TABLE IF EXISTS public.alerts CASCADE;
DROP TABLE IF EXISTS public.anomalyscores CASCADE;

-- ============================================================================
-- PART 2: Create api_logs Table (Primary data source)
-- Purpose: Store ALL API request/response data for ML analysis
-- ============================================================================

CREATE TABLE api_logs (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- API Request Info
    endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL CHECK (http_method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')),
    status_code INTEGER NOT NULL CHECK (status_code >= 100 AND status_code < 600),
    response_time_ms BIGINT NOT NULL CHECK (response_time_ms >= 0),
    
    -- Request/Response Size (bytes)
    request_size_bytes BIGINT,
    response_size_bytes BIGINT,
    
    -- System Metrics
    cpu_usage_percent DOUBLE PRECISION CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
    memory_usage_percent DOUBLE PRECISION CHECK (memory_usage_percent >= 0 AND memory_usage_percent <= 100),
    disk_io_bytes BIGINT,
    network_io_bytes BIGINT,
    
    -- Error Tracking
    error_rate DOUBLE PRECISION DEFAULT 0.0 CHECK (error_rate >= 0 AND error_rate <= 1),
    error_count INTEGER DEFAULT 0,
    error_message TEXT,
    stack_trace TEXT,
    
    -- Request Context
    request_count INTEGER DEFAULT 1 CHECK (request_count > 0),
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Request/Response Bodies (flexible JSON)
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
    environment VARCHAR(50) DEFAULT 'production' CHECK (environment IN ('dev', 'staging', 'production')),
    
    -- Temporal Features (for ML)
    hour_of_day INTEGER CHECK (hour_of_day >= 0 AND hour_of_day < 24),
    day_of_week INTEGER CHECK (day_of_week >= 1 AND day_of_week <= 7),
    is_weekend BOOLEAN,
    is_business_hours BOOLEAN,
    
    -- Processing Status
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMP,
    anomaly_detection_id BIGINT,
    ml_service_version VARCHAR(50),
    
    -- Audit Fields (Enterprise Standard)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255),
    
    -- Metadata (for extensibility)
    metadata JSONB
);

-- Table Comment
COMMENT ON TABLE api_logs IS 'Primary data source: Stores ALL API request/response data for ML-based anomaly detection (Priority 1 Enterprise Integration)';
COMMENT ON COLUMN api_logs.trace_id IS 'Distributed trace identifier for request correlation';
COMMENT ON COLUMN api_logs.is_processed IS 'Flag indicating if this log has been analyzed by ML service';
COMMENT ON COLUMN api_logs.metadata IS 'Flexible JSON field for additional context (custom fields, tags)';

-- Performance Indexes
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_status_code ON api_logs(status_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_trace_id ON api_logs(trace_id) WHERE deleted_at IS NULL;

-- Composite Indexes (common query patterns)
CREATE INDEX idx_api_logs_endpoint_created ON api_logs(endpoint, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_logs_service_created ON api_logs(service_name, created_at DESC) WHERE deleted_at IS NULL;

-- Processing Index (batch operations)
CREATE INDEX idx_api_logs_unprocessed ON api_logs(is_processed, created_at) 
    WHERE deleted_at IS NULL AND is_processed = FALSE;

-- BRIN Index (very efficient for time-series data on large tables)
CREATE INDEX idx_api_logs_created_at_brin ON api_logs USING BRIN(created_at);

-- ============================================================================
-- PART 3: Create anomaly_detections Table (ML Predictions)
-- Purpose: Store ML model predictions and anomaly scores
-- ============================================================================

CREATE TABLE anomaly_detections (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Link to source log
    api_log_id BIGINT REFERENCES api_logs(id) ON DELETE SET NULL,
    
    -- API Info (denormalized for fast queries)
    endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    
    -- ML Model Scores (All three algorithms)
    msif_lstm_score DOUBLE PRECISION NOT NULL CHECK (msif_lstm_score >= 0 AND msif_lstm_score <= 1),
    ple_gru_score DOUBLE PRECISION NOT NULL CHECK (ple_gru_score >= 0 AND ple_gru_score <= 1),
    hybrid_ensemble_score DOUBLE PRECISION NOT NULL CHECK (hybrid_ensemble_score >= 0 AND hybrid_ensemble_score <= 1),
    
    -- Confidence & Severity
    confidence_score DOUBLE PRECISION NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity_level VARCHAR(50) NOT NULL CHECK (severity_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    anomaly_type VARCHAR(100),  -- response_time, error_rate, resource_usage, network, custom
    
    -- ML Model Info
    fusion_method VARCHAR(100) NOT NULL,  -- weighted_ensemble, voting, stacking
    ml_model_version VARCHAR(50),
    ml_processing_time_ms BIGINT,
    
    -- Status Management
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'RESOLVED', 'FALSE_POSITIVE')),
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
    
    -- Audit Fields (Enterprise Standard)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255),
    
    -- Metadata
    additional_context JSONB
);

-- Table Comment
COMMENT ON TABLE anomaly_detections IS 'ML anomaly detection results: Stores predictions from MSIF-LSTM, PLE-GRU, and Hybrid-Ensemble models (Priority 1 Enterprise Integration)';
COMMENT ON COLUMN anomaly_detections.hybrid_ensemble_score IS 'Final score from weighted ensemble of all three models (primary scoring metric)';
COMMENT ON COLUMN anomaly_detections.status IS 'Lifecycle status: ACTIVE (ongoing), RESOLVED (handled), FALSE_POSITIVE (incorrect detection)';

-- Performance Indexes
CREATE INDEX idx_anomaly_detections_endpoint ON anomaly_detections(endpoint) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_severity ON anomaly_detections(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_status ON anomaly_detections(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_created_at ON anomaly_detections(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_trace_id ON anomaly_detections(trace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_anomaly_detections_api_log_id ON anomaly_detections(api_log_id) WHERE deleted_at IS NULL;

-- Composite Indexes (dashboard queries)
CREATE INDEX idx_anomaly_detections_severity_status ON anomaly_detections(severity_level, status, created_at DESC) 
    WHERE deleted_at IS NULL;

-- Hot Query Index (unacknowledged critical anomalies)
CREATE INDEX idx_anomaly_detections_critical_unack ON anomaly_detections(created_at DESC) 
    WHERE deleted_at IS NULL AND is_acknowledged = FALSE AND severity_level IN ('CRITICAL', 'HIGH');

-- ============================================================================
-- PART 4: Create system_metrics Table (Time-series data)
-- Purpose: Store system/service metrics for correlation with anomalies
-- ============================================================================

CREATE TABLE system_metrics (
    id BIGSERIAL PRIMARY KEY,
    
    -- Link to API log (if available)
    api_log_id BIGINT REFERENCES api_logs(id) ON DELETE SET NULL,
    
    -- Service Info
    service_name VARCHAR(255) NOT NULL,
    endpoint VARCHAR(500),
    
    -- Metrics (from original metrics table)
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

-- Table Comment
COMMENT ON TABLE system_metrics IS 'Time-series system metrics: Stores CPU, memory, disk, network metrics for analysis and correlation';

-- Performance Indexes
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(metric_timestamp DESC);
CREATE INDEX idx_system_metrics_service ON system_metrics(service_name, metric_timestamp DESC);
CREATE INDEX idx_system_metrics_api_log_id ON system_metrics(api_log_id) WHERE api_log_id IS NOT NULL;

-- ============================================================================
-- PART 5: Create distributed_traces Table (Distributed Tracing)
-- Purpose: Store distributed tracing data for request correlation
-- ============================================================================

CREATE TABLE distributed_traces (
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

-- Table Comment
COMMENT ON TABLE distributed_traces IS 'Distributed tracing data: Stores spans for request tracing across services';

-- Performance Indexes
CREATE INDEX idx_distributed_traces_trace_id ON distributed_traces(trace_id);
CREATE INDEX idx_distributed_traces_service ON distributed_traces(service_name, start_time DESC);
CREATE INDEX idx_distributed_traces_parent ON distributed_traces(parent_span_id) WHERE parent_span_id IS NOT NULL;
CREATE INDEX idx_distributed_traces_created_at ON distributed_traces(created_at DESC);

-- ============================================================================
-- PART 6: Create alert_rules Table (Alert Configuration)
-- Purpose: Store alert rules and notification configuration
-- ============================================================================

CREATE TABLE alert_rules (
    id BIGSERIAL PRIMARY KEY,
    
    -- Alert Config
    alert_name VARCHAR(255) NOT NULL,
    alert_description TEXT,
    
    -- Condition
    condition_type VARCHAR(100) NOT NULL CHECK (condition_type IN ('threshold', 'anomaly_score', 'error_rate', 'response_time')),
    condition_expression TEXT NOT NULL,
    threshold_value DOUBLE PRECISION,
    
    -- Severity
    severity_level VARCHAR(50) NOT NULL CHECK (severity_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    -- Status
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Notification
    notification_channels JSONB,  -- ["email", "slack", "pagerduty", "webhook"]
    notification_recipients JSONB,
    
    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
);

-- Table Comment
COMMENT ON TABLE alert_rules IS 'Alert rules: Stores alert configuration, thresholds, and notification channels';

-- Performance Indexes
CREATE INDEX idx_alert_rules_enabled ON alert_rules(is_enabled) WHERE deleted_at IS NULL AND is_enabled = TRUE;
CREATE INDEX idx_alert_rules_severity ON alert_rules(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_alert_rules_created_at ON alert_rules(created_at DESC) WHERE deleted_at IS NULL;

-- ============================================================================
-- PART 7: Create Views (Optional - for common queries)
-- ============================================================================

-- Recent anomalies view
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

COMMENT ON VIEW v_recent_anomalies IS 'Recent 100 anomalies for dashboard';

-- Anomaly statistics view
CREATE OR REPLACE VIEW v_anomaly_stats AS
SELECT 
    DATE(a.created_at) as date,
    a.severity_level,
    COUNT(*) as count,
    AVG(a.hybrid_ensemble_score) as avg_score,
    MAX(a.hybrid_ensemble_score) as max_score,
    MIN(a.hybrid_ensemble_score) as min_score,
    SUM(CASE WHEN a.is_acknowledged THEN 1 ELSE 0 END) as acknowledged_count
FROM anomaly_detections a
WHERE a.deleted_at IS NULL
GROUP BY DATE(a.created_at), a.severity_level
ORDER BY date DESC;

COMMENT ON VIEW v_anomaly_stats IS 'Daily anomaly statistics by severity';

-- ============================================================================
-- PART 8: Grant Permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON api_logs TO api_monitor;
GRANT SELECT, INSERT, UPDATE, DELETE ON anomaly_detections TO api_monitor;
GRANT SELECT, INSERT, UPDATE, DELETE ON system_metrics TO api_monitor;
GRANT SELECT, INSERT, UPDATE, DELETE ON distributed_traces TO api_monitor;
GRANT SELECT, INSERT, UPDATE, DELETE ON alert_rules TO api_monitor;
GRANT SELECT ON v_recent_anomalies TO api_monitor;
GRANT SELECT ON v_anomaly_stats TO api_monitor;

-- Grant sequence permissions for auto-increment
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_monitor;

-- ============================================================================
-- PART 9: Migration Notes
-- ============================================================================
-- This migration creates an enterprise-grade schema with:
-- ✅ Proper naming conventions (snake_case, descriptive names)
-- ✅ Audit fields (created_at, created_by, deleted_at for soft deletes)
-- ✅ Performance indexes (single, composite, BRIN)
-- ✅ Constraints (CHECK, NOT NULL, FOREIGN KEY)
-- ✅ Table comments and column documentation
-- ✅ Support for multi-tenancy (can add tenant_id later)
-- ✅ Views for common queries
-- ✅ Proper permissions for api_monitor user
-- 
-- Old tables dropped: anomalies, metrics, traces, alerts, anomalyscores
-- 
-- Data migration: Run V5_1__Migrate_Legacy_Data.sql for data preservation
-- ============================================================================
