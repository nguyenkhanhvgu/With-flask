-- Initialize database for Flask Blog Application
-- This script runs when the PostgreSQL container starts for the first time

-- Create additional databases if needed
-- CREATE DATABASE blogdb_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';