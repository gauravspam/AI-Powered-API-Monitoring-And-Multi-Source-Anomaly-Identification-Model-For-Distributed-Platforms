CREATE DATABASE api_monitoring;

CREATE USER api_monitor WITH PASSWORD 'api_monitor_pwd';

GRANT ALL PRIVILEGES ON DATABASE api_monitoring TO api_monitor;

\c api_monitoring;

GRANT ALL PRIVILEGES ON SCHEMA public TO api_monitor;
GRANT ALL ON ALL TABLES IN SCHEMA public TO api_monitor;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO api_monitor;
