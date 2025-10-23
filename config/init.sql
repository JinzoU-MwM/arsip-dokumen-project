-- AI Legal Document Automation System - Database Initialization
-- This script creates the database and initial setup

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS legal_automation;

-- Switch to the database
\c legal_automation;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For GIN indexes

-- Create indexes for better performance
-- These will be created by SQLAlchemy models, but we can add additional ones

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_documents_text_search ON documents USING gin(to_tsvector('english', text_content));
CREATE INDEX IF NOT EXISTS idx_companies_text_search ON companies USING gin(to_tsvector('english', name || ' ' || COALESCE(business_description, '')));

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_documents_company_type ON documents(company_id, document_type);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_status_type ON notifications(status, notification_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp_user ON audit_logs(timestamp, user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type, timestamp);

-- Create partitioned table for audit logs (if needed in future)
-- Currently using regular table with indexes

-- Create function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create initial admin user (will be replaced by application logic)
-- This is just for development - in production, create users through the application
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'legal_automation_user') THEN
        CREATE USER legal_automation_user WITH PASSWORD 'secure_password_here';
        GRANT ALL PRIVILEGES ON DATABASE legal_automation TO legal_automation_user;
        GRANT ALL ON SCHEMA public TO legal_automation_user;
    END IF;
END
$$;

-- Set up default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO legal_automation_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO legal_automation_user;

-- Create view for active documents
CREATE OR REPLACE VIEW active_documents AS
SELECT
    d.id,
    d.original_filename,
    d.document_type,
    d.status,
    d.compliance_status,
    d.created_at,
    d.processed_at,
    c.name as company_name,
    u.full_name as uploader_name
FROM documents d
JOIN companies c ON d.company_id = c.id
LEFT JOIN users u ON d.uploaded_by = u.id
WHERE d.status IN ('processed', 'validated')
  AND c.is_active = true;

-- Create view for processing statistics
CREATE OR REPLACE VIEW processing_stats AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    status,
    COUNT(*) as count,
    AVG(processing_time) as avg_processing_time
FROM processing_jobs
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), status
ORDER BY date DESC;

-- Grant permissions on views
GRANT SELECT ON active_documents TO legal_automation_user;
GRANT SELECT ON processing_stats TO legal_automation_user;

-- Create trigger functions for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- This will be implemented by the application layer
    -- SQLAlchemy handles the audit logging
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Insert initial system configuration
INSERT INTO system_configurations (config_key, config_value, description, category) VALUES
('max_file_size_mb', '100', 'Maximum file size in MB for document uploads', 'upload'),
('supported_file_types', '["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png"]', 'Supported file types for upload', 'upload'),
('default_retention_days', '2555', 'Default retention period in days (7 years)', 'retention'),
('max_processing_time_minutes', '30', 'Maximum processing time in minutes', 'processing'),
('enable_ai_confidence_threshold', 'true', 'Enable AI confidence threshold checking', 'ai'),
('min_ai_confidence_threshold', '0.8', 'Minimum AI confidence threshold', 'ai'),
('enable_compliance_validation', 'true', 'Enable automatic compliance validation', 'compliance'),
('default_notification_channels', '["whatsapp", "email"]', 'Default notification channels', 'notification'),
('rate_limit_per_minute', '30', 'Rate limit per minute per user', 'security')
ON CONFLICT (config_key) DO NOTHING;

-- Create materialized view for document compliance dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS compliance_dashboard AS
SELECT
    c.id as company_id,
    c.name as company_name,
    COUNT(d.id) as total_documents,
    COUNT(CASE WHEN d.status = 'processed' THEN 1 END) as processed_documents,
    COUNT(CASE WHEN d.compliance_status = 'compliant' THEN 1 END) as compliant_documents,
    COUNT(CASE WHEN d.compliance_status = 'non_compliant' THEN 1 END) as non_compliant_documents,
    COUNT(CASE WHEN d.compliance_status = 'requires_review' THEN 1 END) as requires_review_documents,
    AVG(d.compliance_score) as avg_compliance_score,
    MAX(d.updated_at) as last_document_update
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
WHERE c.is_active = true
GROUP BY c.id, c.name;

-- Create unique index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_compliance_dashboard_company_id
ON compliance_dashboard (company_id);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_compliance_dashboard()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY compliance_dashboard;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions on materialized view
GRANT SELECT ON compliance_dashboard TO legal_automation_user;

-- Set up automated refresh (this would typically be handled by a cron job)
-- For development, manual refresh: SELECT refresh_compliance_dashboard();

-- Create database health check function
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS JSON AS $$
DECLARE
    result JSON;
    table_count INTEGER;
    total_documents INTEGER;
    total_users INTEGER;
    recent_activities INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public';

    -- Count documents
    SELECT COUNT(*) INTO total_documents
    FROM documents;

    -- Count users
    SELECT COUNT(*) INTO total_users
    FROM users;

    -- Count recent activities (last 24 hours)
    SELECT COUNT(*) INTO recent_activities
    FROM audit_logs
    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours';

    -- Build result JSON
    result := json_build_object(
        'status', 'healthy',
        'table_count', table_count,
        'total_documents', total_documents,
        'total_users', total_users,
        'recent_activities_24h', recent_activities,
        'timestamp', CURRENT_TIMESTAMP
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Add comment to database
COMMENT ON DATABASE legal_automation IS 'AI Legal Document Automation System Database';

-- Output completion message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE 'Database: legal_automation';
    RAISE NOTICE 'Extensions created: uuid-ossp, pg_trgm, btree_gin';
    RAISE NOTICE 'Indexes created for performance optimization';
    RAISE NOTICE 'Views created: active_documents, processing_stats, compliance_dashboard';
    RAISE NOTICE 'Initial system configuration inserted';
END $$;