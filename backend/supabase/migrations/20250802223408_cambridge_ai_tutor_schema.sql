BEGIN;

-- Create custom types for the Cambridge AI Tutor
CREATE TYPE user_role AS ENUM ('parent', 'child', 'admin');
CREATE TYPE subject_type AS ENUM ('mathematics', 'esl', 'science');
CREATE TYPE learning_style AS ENUM ('visual', 'auditory', 'kinesthetic', 'mixed');
CREATE TYPE difficulty_level AS ENUM ('beginner', 'elementary', 'intermediate', 'advanced', 'expert');
CREATE TYPE activity_type AS ENUM ('lesson', 'practice', 'assessment', 'game', 'explanation', 'question');

-- User profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS tutor_user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Child profiles with learning preferences and safety settings
CREATE TABLE IF NOT EXISTS tutor_child_profiles (
    child_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES tutor_user_profiles(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 5 AND age <= 12),
    grade_level INTEGER NOT NULL CHECK (grade_level >= 1 AND grade_level <= 6),
    learning_style VARCHAR(20) DEFAULT 'mixed',
    preferred_subjects subject_type[] DEFAULT '{}',
    learning_preferences JSONB DEFAULT '{}',
    curriculum_progress JSONB DEFAULT '{}',
    safety_settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_name CHECK (LENGTH(TRIM(name)) > 0)
);

-- Parent profiles
CREATE TABLE IF NOT EXISTS tutor_parent_profiles (
    parent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES tutor_user_profiles(user_id) ON DELETE CASCADE,
    children_ids UUID[] DEFAULT '{}',
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_preferences JSONB DEFAULT '{}',
    guidance_level VARCHAR(20) DEFAULT 'intermediate',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_guidance_level CHECK (guidance_level IN ('beginner', 'intermediate', 'advanced'))
);

-- Cambridge curriculum topics
CREATE TABLE IF NOT EXISTS tutor_curriculum_topics (
    topic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject subject_type NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level >= 1 AND grade_level <= 6),
    cambridge_code VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    prerequisites UUID[] DEFAULT '{}',
    learning_objectives TEXT[] DEFAULT '{}',
    difficulty_level VARCHAR(20) DEFAULT 'elementary',
    estimated_duration_minutes INTEGER DEFAULT 30 CHECK (estimated_duration_minutes >= 5 AND estimated_duration_minutes <= 120),
    content_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_title CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT valid_cambridge_code CHECK (LENGTH(TRIM(cambridge_code)) >= 3)
);

-- Learning objectives
CREATE TABLE IF NOT EXISTS tutor_learning_objectives (
    objective_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES tutor_curriculum_topics(topic_id) ON DELETE CASCADE,
    description VARCHAR(500) NOT NULL,
    cambridge_reference VARCHAR(100),
    assessment_criteria TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_description CHECK (LENGTH(TRIM(description)) > 0)
);

-- Educational content items
CREATE TABLE IF NOT EXISTS tutor_content_items (
    content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES tutor_curriculum_topics(topic_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content_data JSONB DEFAULT '{}',
    difficulty_level VARCHAR(20) DEFAULT 'elementary',
    age_appropriateness JSONB DEFAULT '{}',
    curriculum_alignment JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_content_title CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT valid_content_type CHECK (content_type IN ('text', 'video', 'image', 'interactive', 'game'))
);

-- Learning activities and interactions
CREATE TABLE IF NOT EXISTS tutor_learning_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES tutor_curriculum_topics(topic_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    content JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_minutes INTEGER CHECK (duration_minutes >= 0),
    performance_data JSONB DEFAULT '{}',
    is_completed BOOLEAN DEFAULT FALSE
);

-- AI tutor sessions
CREATE TABLE IF NOT EXISTS tutor_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    context JSONB DEFAULT '{}',
    learning_outcomes TEXT[] DEFAULT '{}',
    message_count INTEGER DEFAULT 0
);

-- Tutor messages within sessions
CREATE TABLE IF NOT EXISTS tutor_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES tutor_sessions(session_id) ON DELETE CASCADE,
    sender VARCHAR(10) NOT NULL CHECK (sender IN ('user', 'tutor')),
    content TEXT NOT NULL,
    message_type VARCHAR(10) DEFAULT 'text' CHECK (message_type IN ('text', 'voice', 'image')),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Progress tracking records
CREATE TABLE IF NOT EXISTS tutor_progress_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES tutor_curriculum_topics(topic_id) ON DELETE CASCADE,
    skill_level DECIMAL(3,2) CHECK (skill_level >= 0 AND skill_level <= 1),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    last_practiced TIMESTAMPTZ DEFAULT NOW(),
    mastery_indicators JSONB DEFAULT '{}',
    improvement_areas TEXT[] DEFAULT '{}',
    
    UNIQUE(user_id, topic_id)
);

-- Assessments
CREATE TABLE IF NOT EXISTS tutor_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES tutor_curriculum_topics(topic_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    questions JSONB DEFAULT '[]',
    total_points INTEGER DEFAULT 100 CHECK (total_points >= 1),
    passing_score INTEGER DEFAULT 70 CHECK (passing_score >= 1),
    time_limit_minutes INTEGER CHECK (time_limit_minutes > 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_assessment_title CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT valid_passing_score CHECK (passing_score <= total_points)
);

-- Assessment results
CREATE TABLE IF NOT EXISTS tutor_assessment_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES tutor_assessments(assessment_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0 CHECK (score >= 0),
    total_possible INTEGER DEFAULT 100 CHECK (total_possible >= 1),
    percentage DECIMAL(5,2) DEFAULT 0 CHECK (percentage >= 0 AND percentage <= 100),
    passed BOOLEAN DEFAULT FALSE,
    answers JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

-- User sessions for multi-device support
CREATE TABLE IF NOT EXISTS tutor_user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES tutor_child_profiles(child_id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('web', 'mobile', 'extension')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending', 'conflict'))
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_child_profiles_parent_id ON tutor_child_profiles(parent_id);
CREATE INDEX IF NOT EXISTS idx_child_profiles_age ON tutor_child_profiles(age);
CREATE INDEX IF NOT EXISTS idx_child_profiles_grade_level ON tutor_child_profiles(grade_level);

CREATE INDEX IF NOT EXISTS idx_curriculum_topics_subject ON tutor_curriculum_topics(subject);
CREATE INDEX IF NOT EXISTS idx_curriculum_topics_grade_level ON tutor_curriculum_topics(grade_level);
CREATE INDEX IF NOT EXISTS idx_curriculum_topics_cambridge_code ON tutor_curriculum_topics(cambridge_code);

CREATE INDEX IF NOT EXISTS idx_learning_activities_user_id ON tutor_learning_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_activities_topic_id ON tutor_learning_activities(topic_id);
CREATE INDEX IF NOT EXISTS idx_learning_activities_started_at ON tutor_learning_activities(started_at);
CREATE INDEX IF NOT EXISTS idx_learning_activities_completed ON tutor_learning_activities(is_completed);

CREATE INDEX IF NOT EXISTS idx_tutor_sessions_user_id ON tutor_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_tutor_sessions_started_at ON tutor_sessions(started_at);

CREATE INDEX IF NOT EXISTS idx_tutor_messages_session_id ON tutor_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_tutor_messages_timestamp ON tutor_messages(timestamp);

CREATE INDEX IF NOT EXISTS idx_progress_records_user_id ON tutor_progress_records(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_records_topic_id ON tutor_progress_records(topic_id);
CREATE INDEX IF NOT EXISTS idx_progress_records_last_practiced ON tutor_progress_records(last_practiced);

CREATE INDEX IF NOT EXISTS idx_assessment_results_user_id ON tutor_assessment_results(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_results_assessment_id ON tutor_assessment_results(assessment_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON tutor_user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON tutor_user_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON tutor_user_sessions(is_active);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE tutor_user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_child_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_parent_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_curriculum_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_learning_objectives ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_content_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_learning_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_progress_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_assessment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_user_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user access control
-- User profiles - users can only access their own profile
CREATE POLICY tutor_user_profiles_policy ON tutor_user_profiles
    FOR ALL
    USING (auth.uid() = user_id);

-- Child profiles - parents can access their children's profiles
CREATE POLICY tutor_child_profiles_policy ON tutor_child_profiles
    FOR ALL
    USING (
        parent_id = auth.uid() OR 
        child_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Parent profiles - parents can access their own profiles
CREATE POLICY tutor_parent_profiles_policy ON tutor_parent_profiles
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Curriculum topics - accessible to all authenticated users (read-only for most)
CREATE POLICY tutor_curriculum_topics_read_policy ON tutor_curriculum_topics
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY tutor_curriculum_topics_write_policy ON tutor_curriculum_topics
    FOR INSERT, UPDATE, DELETE
    USING (
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Learning activities - children and their parents can access
CREATE POLICY tutor_learning_activities_policy ON tutor_learning_activities
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = user_id AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Tutor sessions - children and their parents can access
CREATE POLICY tutor_sessions_policy ON tutor_sessions
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = user_id AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Tutor messages - access through session ownership
CREATE POLICY tutor_messages_policy ON tutor_messages
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM tutor_sessions s
            WHERE s.session_id = tutor_messages.session_id
            AND (
                s.user_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM tutor_child_profiles 
                    WHERE child_id = s.user_id AND parent_id = auth.uid()
                ) OR
                EXISTS (
                    SELECT 1 FROM tutor_user_profiles 
                    WHERE user_id = auth.uid() AND role = 'admin'
                )
            )
        )
    );

-- Progress records - children and their parents can access
CREATE POLICY tutor_progress_records_policy ON tutor_progress_records
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = user_id AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Assessment results - children and their parents can access
CREATE POLICY tutor_assessment_results_policy ON tutor_assessment_results
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = user_id AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- User sessions - users can access their own sessions
CREATE POLICY tutor_user_sessions_policy ON tutor_user_sessions
    FOR ALL
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM tutor_child_profiles 
            WHERE child_id = user_id AND parent_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM tutor_user_profiles 
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tutor_user_profiles_updated_at
    BEFORE UPDATE ON tutor_user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutor_child_profiles_updated_at
    BEFORE UPDATE ON tutor_child_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutor_parent_profiles_updated_at
    BEFORE UPDATE ON tutor_parent_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutor_curriculum_topics_updated_at
    BEFORE UPDATE ON tutor_curriculum_topics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutor_content_items_updated_at
    BEFORE UPDATE ON tutor_content_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated, service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;

-- Add comments for documentation
COMMENT ON TABLE tutor_user_profiles IS 'User profiles for the Cambridge AI Tutor system';
COMMENT ON TABLE tutor_child_profiles IS 'Child profiles with learning preferences and safety settings';
COMMENT ON TABLE tutor_parent_profiles IS 'Parent profiles with children management and preferences';
COMMENT ON TABLE tutor_curriculum_topics IS 'Cambridge curriculum topics and learning objectives';
COMMENT ON TABLE tutor_learning_activities IS 'Learning activities and interactions tracking';
COMMENT ON TABLE tutor_sessions IS 'AI tutor conversation sessions';
COMMENT ON TABLE tutor_messages IS 'Messages within tutor sessions';
COMMENT ON TABLE tutor_progress_records IS 'Learning progress tracking for each child and topic';
COMMENT ON TABLE tutor_assessments IS 'Assessments and quizzes';
COMMENT ON TABLE tutor_assessment_results IS 'Results from completed assessments';
COMMENT ON TABLE tutor_user_sessions IS 'Multi-device session management';

COMMIT;