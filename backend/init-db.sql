-- SkyRide PostgreSQL Database Initialization
-- Creates necessary extensions and initial configuration

-- Enable UUID extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable PostGIS extension for geospatial data (future use)
-- CREATE EXTENSION IF NOT EXISTS "postgis";

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS skyride;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default schema
ALTER DATABASE skyride SET search_path TO skyride, public;

-- Create initial admin user (if needed)
-- This can be used for application-level user management
INSERT INTO public.users (id, email, role, active, created_at)
VALUES (
    uuid_generate_v4(),
    'admin@skyride.city',
    'admin',
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Create indexes for performance
-- Note: These will be created by Alembic migrations, but we can add custom ones here

-- Logging function for database operations
CREATE OR REPLACE FUNCTION log_table_changes()
RETURNS trigger AS $$
BEGIN
    -- Log changes to analytics schema
    INSERT INTO analytics.change_log (
        table_name,
        operation,
        old_data,
        new_data,
        changed_by,
        changed_at
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        current_user,
        NOW()
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Initial configuration settings
CREATE TABLE IF NOT EXISTS skyride.app_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default configuration
INSERT INTO skyride.app_config (key, value, description) VALUES
    ('platform_name', 'SkyRide', 'Platform display name'),
    ('default_currency', 'USD', 'Default currency for pricing'),
    ('default_timezone', 'America/Panama', 'Default timezone'),
    ('booking_hold_duration', '1440', 'Default hold duration in minutes (24 hours)'),
    ('quote_expiration', '2880', 'Default quote expiration in minutes (48 hours)'),
    ('service_fee_rate', '0.05', 'Default service fee rate (5%)'),
    ('platform_version', '2.0.0', 'Current platform version')
ON CONFLICT (key) DO NOTHING;

-- Analytics schema tables
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.change_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_change_log_table_date 
ON analytics.change_log (table_name, changed_at);

CREATE INDEX IF NOT EXISTS idx_change_log_operation 
ON analytics.change_log (operation, changed_at);

-- Performance monitoring views
CREATE OR REPLACE VIEW analytics.table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname IN ('skyride', 'public')
ORDER BY size_bytes DESC;

CREATE OR REPLACE VIEW analytics.query_performance AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_time DESC
LIMIT 20;

-- Grant permissions
-- GRANT ALL PRIVILEGES ON SCHEMA skyride TO skyride_user;
-- GRANT ALL PRIVILEGES ON SCHEMA analytics TO skyride_user;

COMMENT ON DATABASE skyride IS 'SkyRide Charter Booking Platform - Production Database';
COMMENT ON SCHEMA skyride IS 'Main application schema for SkyRide platform';
COMMENT ON SCHEMA analytics IS 'Analytics and monitoring schema for performance tracking';