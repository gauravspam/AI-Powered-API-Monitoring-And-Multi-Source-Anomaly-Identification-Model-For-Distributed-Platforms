CREATE ROLE api_monitor WITH LOGIN PASSWORD 'api_monitor_pwd';
GRANT ALL PRIVILEGES ON DATABASE api_monitoring TO api_monitor;
GRANT ALL ON SCHEMA public TO api_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO api_monitor;
