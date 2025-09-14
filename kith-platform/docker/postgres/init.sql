-- Initialize PostgreSQL database for Kith Platform
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can add any additional setup here

-- Set timezone
SET timezone = 'UTC';

-- Create any additional users or permissions if needed
-- (The main user is created by the POSTGRES_USER env var)
