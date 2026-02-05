CREATE TABLE IF NOT EXISTS traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(100) NOT NULL,
    span_id VARCHAR(100),
    parent_span_id VARCHAR(100),
    service_name VARCHAR(255) NOT NULL,
    operation_name VARCHAR(255),
    duration_ms BIGINT,
    status_code INTEGER,
    timestamp TIMESTAMP NOT NULL,
    tags TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_trace_id ON traces(trace_id);
CREATE INDEX idx_service_name ON traces(service_name);
CREATE INDEX idx_timestamp ON traces(timestamp DESC);
CREATE INDEX idx_trace_service_time ON traces(service_name, timestamp DESC);

-- Comments
COMMENT ON TABLE traces IS 'Distributed tracing data storage';
COMMENT ON COLUMN traces.trace_id IS 'Unique trace identifier across services';
COMMENT ON COLUMN traces.span_id IS 'Individual span identifier within trace';
COMMENT ON COLUMN traces.parent_span_id IS 'Parent span for hierarchical traces';
COMMENT ON COLUMN traces.duration_ms IS 'Span duration in milliseconds';
