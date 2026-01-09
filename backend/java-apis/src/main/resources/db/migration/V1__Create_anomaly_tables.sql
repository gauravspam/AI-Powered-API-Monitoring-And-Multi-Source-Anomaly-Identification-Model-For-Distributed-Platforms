-- Flyway Migration: V1__Create_anomaly_tables.sql

CREATE TABLE anomaly_scores (
    id BIGSERIAL PRIMARY KEY,
    api_endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    anomaly_type VARCHAR(50) NOT NULL,
    score FLOAT NOT NULL,
    severity VARCHAR(20),
    timestamp TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_endpoint ON anomaly_scores(api_endpoint);
CREATE INDEX idx_anomaly_type ON anomaly_scores(anomaly_type);
CREATE INDEX idx_severity ON anomaly_scores(severity);
CREATE INDEX idx_timestamp ON anomaly_scores(timestamp);
CREATE INDEX idx_api_timestamp ON anomaly_scores(api_endpoint, timestamp);
CREATE INDEX idx_created_at ON anomaly_scores(created_at);

CREATE TABLE api_metrics (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    status_code INTEGER,
    response_time_ms BIGINT,
    request_count INTEGER DEFAULT 1,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_endpoint ON api_metrics(endpoint);
CREATE INDEX idx_status_code ON api_metrics(status_code);
CREATE INDEX idx_response_time ON api_metrics(response_time_ms);
CREATE INDEX idx_metrics_timestamp ON api_metrics(timestamp);
CREATE INDEX idx_endpoint_timestamp ON api_metrics(endpoint, timestamp);
CREATE INDEX idx_metrics_created_at ON api_metrics(created_at);

CREATE TABLE api_traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL UNIQUE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    request_body TEXT,
    response_body TEXT,
    error_details TEXT,
    response_time_ms BIGINT,
    timestamp TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trace_id ON api_traces(trace_id);
CREATE INDEX idx_trace_endpoint ON api_traces(endpoint);
CREATE INDEX idx_trace_timestamp ON api_traces(timestamp);
CREATE INDEX idx_trace_created_at ON api_traces(created_at);

CREATE VIEW v_recent_anomalies AS
SELECT 
    id,
    api_endpoint,
    method,
    anomaly_type,
    score,
    severity,
    timestamp,
    created_at
FROM anomaly_scores
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC;

CREATE VIEW v_anomaly_stats AS
SELECT 
    anomaly_type,
    severity,
    COUNT(*) as count,
    AVG(score) as avg_score,
    MAX(score) as max_score,
    MIN(score) as min_score,
    DATE(created_at) as date
FROM anomaly_scores
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY anomaly_type, severity, DATE(created_at);

CREATE VIEW v_api_performance AS
SELECT 
    endpoint,
    method,
    COUNT(*) as total_requests,
    AVG(response_time_ms) as avg_response_time,
    MAX(response_time_ms) as max_response_time,
    MIN(response_time_ms) as min_response_time,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    DATE(created_at) as date
FROM api_metrics
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY endpoint, method, DATE(created_at);