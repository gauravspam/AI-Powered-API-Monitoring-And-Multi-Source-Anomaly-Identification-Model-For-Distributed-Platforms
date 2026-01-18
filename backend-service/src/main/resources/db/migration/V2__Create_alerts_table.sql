CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    anomaly_score DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_alerts_api_name ON alerts(api_name);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
