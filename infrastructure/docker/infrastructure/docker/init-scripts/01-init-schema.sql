CREATE DATABASE api_monitoring;
CREATE USER api_monitor WITH PASSWORD 'api_monitor_pwd';
GRANT ALL PRIVILEGES ON DATABASE api_monitoring TO api_monitor;
