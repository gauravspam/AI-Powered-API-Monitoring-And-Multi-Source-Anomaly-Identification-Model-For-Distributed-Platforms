CREATE TABLE IF NOT EXISTS alert_rules (
  id BIGSERIAL PRIMARY KEY,
  api_name VARCHAR(255),
  severity VARCHAR(20) NOT NULL,
  threshold DOUBLE PRECISION,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_api_name ON alert_rules(api_name);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);
