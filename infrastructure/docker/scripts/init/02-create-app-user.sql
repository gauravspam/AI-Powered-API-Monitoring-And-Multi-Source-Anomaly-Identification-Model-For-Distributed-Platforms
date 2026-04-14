-- Create application user and grant privileges
-- Run this after 01-init-schema.sql

-- Create the application user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles
        WHERE  rolname = 'api_monitor'
    ) THEN
        CREATE USER api_monitor WITH PASSWORD 'api_monitor_secure_password';
    END IF;
END
$$;

-- Grant privileges on the database
GRANT ALL PRIVILEGES ON DATABASE api_monitoring TO api_monitor;

-- Connect to the database and grant schema privileges
\connect api_monitoring;

GRANT ALL ON SCHEMA public TO api_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO api_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO api_monitor;

-- Grant privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO api_monitor;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO api_monitor;
