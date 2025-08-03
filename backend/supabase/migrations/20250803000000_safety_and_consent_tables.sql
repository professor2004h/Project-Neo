BEGIN;

-- Create custom types for safety and consent tracking
CREATE TYPE consent_type AS ENUM (
    'profile_creation',
    'data_collection', 
    'content_access',
    'voice_interaction',
    'progress_sharing'
);

CREATE TYPE violation_type AS ENUM (
    'inappropriate_content',
    'excessive_session_time',
    'unauthorized_access',
    'privacy_breach'
);

CREATE TYPE violation_severity AS ENUM ('low', 'medium', 'high', 'critical');

-- Parental consent tracking table
CREATE TABLE IF NOT EXISTS tutor_parental_consent (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES tutor_user_profiles(user_id) ON DELETE CASCADE,
    child_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(parent_id, child_id, consent_type)
);

-- Safety violation tracking table
CREATE TABLE IF NOT EXISTS tutor_safety_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    severity violation_severity DEFAULT 'medium',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    parent_notified BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_description CHECK (LENGTH(TRIM(description)) > 0)
);

-- Session time tracking for safety limits
CREATE TABLE IF NOT EXISTS tutor_session_time_tracking (
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES tutor_user_sessions(session_id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    duration_minutes INTEGER NOT NULL DEFAULT 0 CHECK (duration_minutes >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(child_id, session_id)
);

-- Daily usage summary for quick lookups
CREATE TABLE IF NOT EXISTS tutor_daily_usage_summary (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_minutes INTEGER NOT NULL DEFAULT 0 CHECK (total_minutes >= 0),
    session_count INTEGER NOT NULL DEFAULT 0 CHECK (session_count >= 0),
    violations_count INTEGER NOT NULL DEFAULT 0 CHECK (violations_count >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(child_id, date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_parental_consent_parent_child ON tutor_parental_consent(parent_id, child_id);
CREATE INDEX IF NOT EXISTS idx_parental_consent_type ON tutor_parental_consent(consent_type);
CREATE INDEX IF NOT EXISTS idx_parental_consent_granted ON tutor_parental_consent(granted);
CREATE INDEX IF NOT EXISTS idx_parental_consent_expires ON tutor_parental_consent(expires_at);

CREATE INDEX IF NOT EXISTS idx_safety_violations_child_id ON tutor_safety_violations(child_id);
CREATE INDEX IF NOT EXISTS idx_safety_violations_type ON tutor_safety_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_safety_violations_severity ON tutor_safety_violations(severity);
CREATE INDEX IF NOT EXISTS idx_safety_violations_detected_at ON tutor_safety_violations(detected_at);
CREATE INDEX IF NOT EXISTS idx_safety_violations_resolved ON tutor_safety_violations(resolved);

CREATE INDEX IF NOT EXISTS idx_session_time_tracking_child_date ON tutor_session_time_tracking(child_id, date);
CREATE INDEX IF NOT EXISTS idx_session_time_tracking_session ON tutor_session_time_tracking(session_id);

CREATE INDEX IF NOT EXISTS idx_daily_usage_summary_child_date ON tutor_daily_usage_summary(child_id, date);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE tutor_parental_consent ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_safety_violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_session_time_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_daily_usage_summary ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for safety and consent tables

-- Parental consent - parents can access their own consent records
CREATE POLICY tutor_parental_consent_policy ON tutor_parental_consent
    FOR ALL
    USING (
        parent_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Safety violations - parents can access their children's violations
CREATE POLICY tutor_safety_violations_policy ON tutor_safety_violations
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = tutor_safety_violations.child_id 
            AND parent_id = auth.uid()
        ) OR
        child_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Session time tracking - parents and children can access their own data
CREATE POLICY tutor_session_time_tracking_policy ON tutor_session_time_tracking
    FOR ALL
    USING (
        child_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = tutor_session_time_tracking.child_id 
            AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Daily usage summary - parents and children can access their own data
CREATE POLICY tutor_daily_usage_summary_policy ON tutor_daily_usage_summary
    FOR ALL
    USING (
        child_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = tutor_daily_usage_summary.child_id 
            AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Create triggers for updating timestamps
CREATE TRIGGER update_tutor_daily_usage_summary_updated_at
    BEFORE UPDATE ON tutor_daily_usage_summary
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to automatically update daily usage summary
CREATE OR REPLACE FUNCTION update_daily_usage_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert or update daily usage summary
    INSERT INTO tutor_daily_usage_summary (child_id, date, total_minutes, session_count)
    VALUES (NEW.child_id, NEW.date, NEW.duration_minutes, 1)
    ON CONFLICT (child_id, date)
    DO UPDATE SET
        total_minutes = tutor_daily_usage_summary.total_minutes + NEW.duration_minutes,
        session_count = tutor_daily_usage_summary.session_count + 1,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update daily usage summary
CREATE TRIGGER trigger_update_daily_usage_summary
    AFTER INSERT ON tutor_session_time_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_usage_summary();

-- Create function to automatically update violations count in daily summary
CREATE OR REPLACE FUNCTION update_violations_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update violations count in daily usage summary
    INSERT INTO tutor_daily_usage_summary (child_id, date, violations_count)
    VALUES (NEW.child_id, DATE(NEW.detected_at), 1)
    ON CONFLICT (child_id, date)
    DO UPDATE SET
        violations_count = tutor_daily_usage_summary.violations_count + 1,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update violations count
CREATE TRIGGER trigger_update_violations_count
    AFTER INSERT ON tutor_safety_violations
    FOR EACH ROW
    EXECUTE FUNCTION update_violations_count();

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated, service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;

-- Add comments for documentation
COMMENT ON TABLE tutor_parental_consent IS 'Tracking parental consent for various child activities';
COMMENT ON TABLE tutor_safety_violations IS 'Recording safety violations and inappropriate behavior';
COMMENT ON TABLE tutor_session_time_tracking IS 'Tracking session duration for time limit enforcement';
COMMENT ON TABLE tutor_daily_usage_summary IS 'Daily summary of child usage and violations for quick access';

COMMIT;