CREATE USER api_monitor WITH PASSWORD 'api_monitor_pwd';
GRANT ALL PRIVILEGES ON DATABASE api_monitoring TO api_monitor;
\connect api_monitoring;
GRANT ALL ON SCHEMA public TO api_monitor;
