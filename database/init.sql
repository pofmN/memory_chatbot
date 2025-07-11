-- Restructured database schema for memory_chat application (Multi-User Support)
-- This includes tables for multiple users, chat sessions, notifications, alerts, events, and activities

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table (replaces user_profile for multi-user support)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    year_of_birth INTEGER,
    address TEXT,
    major VARCHAR(100),
    additional_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table (now linked to users)
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id UUID NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create chat_messages table (unchanged but now inherits user_id through session)
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    content TEXT,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create chat_summaries table (unchanged but now inherits user_id through session)
CREATE TABLE IF NOT EXISTS chat_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    summarize TEXT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create activities table (now user-specific)
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create activities_analysis table (now user-specific)
CREATE TABLE IF NOT EXISTS activities_analysis (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    preferred_time VARCHAR(20),
    frequency_per_week INTEGER DEFAULT 0,
    frequency_per_month INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT 'No description provided',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create event table (now user-specific)
CREATE TABLE IF NOT EXISTS event (
    event_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location VARCHAR(100),
    priority VARCHAR(20),
    description TEXT,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create recommendation table (now user-specific)
CREATE TABLE IF NOT EXISTS recommendation (
    recommendation_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id VARCHAR(100),
    recommendation_type VARCHAR(50),
    title VARCHAR(100),
    content TEXT,
    score FLOAT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_at TIMESTAMP,
    status VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE SET NULL
);

-- Create alert table (now user-specific)
CREATE TABLE IF NOT EXISTS alert (
    alert_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    activity_analysis_id INTEGER,
    event_id INTEGER,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    trigger_time TIMESTAMP NOT NULL,
    recurrence VARCHAR(50),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    source VARCHAR(50) NOT NULL DEFAULT 'llm',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (activity_analysis_id) REFERENCES activities_analysis(id) ON DELETE SET NULL,
    FOREIGN KEY (event_id) REFERENCES event(event_id) ON DELETE SET NULL
);

-- Create notification_history table (now user-specific)
CREATE TABLE IF NOT EXISTS notification_history (
    notification_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    alert_id INTEGER,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (alert_id) REFERENCES alert(alert_id) ON DELETE SET NULL
);

-- Create fcm_tokens table (now properly linked to users)
CREATE TABLE IF NOT EXISTS fcm_tokens (
    token_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    token TEXT NOT NULL UNIQUE,
    device_type VARCHAR(50) DEFAULT 'web',
    device_info TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create user_sessions table (for session management)
CREATE TABLE IF NOT EXISTS user_sessions (
    session_token UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    device_info TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create views for multi-user support
CREATE OR REPLACE VIEW pending_alerts_view AS
SELECT a.alert_id, a.user_id, a.title, a.message, a.priority, a.trigger_time 
FROM alert a 
WHERE a.status = 'pending' 
AND a.trigger_time <= NOW() + INTERVAL '30 minutes'
ORDER BY a.priority DESC, a.trigger_time ASC;

CREATE OR REPLACE VIEW upcoming_events_view AS
SELECT e.event_id, e.user_id, e.event_name, e.start_time, e.end_time, e.location, e.priority
FROM event e
WHERE e.start_time > NOW()
AND e.start_time <= NOW() + INTERVAL '7 days'
ORDER BY e.start_time ASC;

-- Create user-specific views
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    u.user_id,
    u.username,
    COUNT(DISTINCT a.id) as total_activities,
    COUNT(DISTINCT e.event_id) as total_events,
    COUNT(DISTINCT al.alert_id) as total_alerts,
    COUNT(DISTINCT cs.session_id) as total_sessions
FROM users u
LEFT JOIN activities a ON u.user_id = a.user_id
LEFT JOIN event e ON u.user_id = e.user_id
LEFT JOIN alert al ON u.user_id = al.user_id
LEFT JOIN chat_sessions cs ON u.user_id = cs.user_id
GROUP BY u.user_id, u.username;

-- Function to clean up old alerts (now user-specific)
CREATE OR REPLACE FUNCTION cleanup_old_alerts(target_user_id UUID DEFAULT NULL, days_threshold INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    IF target_user_id IS NULL THEN
        -- Clean up for all users
        DELETE FROM alert 
        WHERE status = 'sent' 
        AND created_at < NOW() - (days_threshold * INTERVAL '1 day');
    ELSE
        -- Clean up for specific user
        DELETE FROM alert 
        WHERE user_id = target_user_id
        AND status = 'sent' 
        AND created_at < NOW() - (days_threshold * INTERVAL '1 day');
    END IF;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user by ID or create default user
CREATE OR REPLACE FUNCTION get_or_create_default_user()
RETURNS UUID AS $$
DECLARE
    default_user_id UUID;
BEGIN
    -- Try to get existing default user
    SELECT user_id INTO default_user_id 
    FROM users 
    WHERE username = 'default_user' 
    LIMIT 1;
    
    -- If no default user exists, create one
    IF default_user_id IS NULL THEN
        INSERT INTO users (username, email, additional_info)
        VALUES ('default_user', 'default@example.com', 'Default system user')
        RETURNING user_id INTO default_user_id;
    END IF;
    
    RETURN default_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance (updated for multi-user)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_start_time ON chat_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_summaries_session_id ON chat_summaries(session_id);

CREATE INDEX IF NOT EXISTS idx_activities_user_id ON activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_start_at ON activities(start_at);
CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_tags ON activities USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_activities_analysis_user_id ON activities_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_analysis_activity_type ON activities_analysis(activity_type);

CREATE INDEX IF NOT EXISTS idx_event_user_id ON event(user_id);
CREATE INDEX IF NOT EXISTS idx_event_start_time ON event(start_time);

CREATE INDEX IF NOT EXISTS idx_recommendation_user_id ON recommendation(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_session_id ON recommendation(session_id);

CREATE INDEX IF NOT EXISTS idx_alert_user_id ON alert(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_trigger_time ON alert(trigger_time);
CREATE INDEX IF NOT EXISTS idx_alert_status ON alert(status);

CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_alert_id ON notification_history(alert_id);

CREATE INDEX IF NOT EXISTS idx_fcm_tokens_user_id ON fcm_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_is_active ON fcm_tokens(is_active);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- Insert default user for testing (hardcoded UUID)
INSERT INTO users (user_id, username, email, additional_info, created_at)
VALUES (
    '12345678-1234-1234-1234-123456789012'::UUID,
    'default_user',
    'default@example.com',
    'Default system user for testing',
    CURRENT_TIMESTAMP
) ON CONFLICT (username) DO NOTHING;

-- Set this as a constant for use in application
-- Default User ID: 12345678-1234-1234-1234-123456789012