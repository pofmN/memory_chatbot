-- Restructured database schema for memory_chat application
-- This includes tables for user profile, chat sessions, notifications, alerts, events, and activities

-- Create user_profile table (single user)
CREATE TABLE IF NOT EXISTS user_profile (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    year_of_birth INTEGER,
    address TEXT,
    major VARCHAR(100),
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    content TEXT,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create chat_summaries table
CREATE TABLE IF NOT EXISTS chat_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    summarize TEXT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create activities table
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Create activities_analysis table
CREATE TABLE IF NOT EXISTS activities_analysis (
    id SERIAL PRIMARY KEY,
    activity_type VARCHAR(100) NOT NULL,
    preferred_time VARCHAR(20),
    frequency_per_week INTEGER DEFAULT 0,
    frequency_per_month INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT 'No description provided'
);

-- Create event table
CREATE TABLE IF NOT EXISTS event (
    event_id SERIAL PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location VARCHAR(100),
    priority VARCHAR(20),
    description TEXT,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create recommendation table
CREATE TABLE IF NOT EXISTS recommendation (
    recommendation_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    recommendation_type VARCHAR(50),
    title VARCHAR(100),
    content TEXT,
    score FLOAT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_at TIMESTAMP,
    status VARCHAR(20),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE SET NULL
);

-- Create alert table
CREATE TABLE IF NOT EXISTS alert (
    alert_id SERIAL PRIMARY KEY,
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
    FOREIGN KEY (activity_analysis_id) REFERENCES activities_analysis(id) ON DELETE SET NULL,
    FOREIGN KEY (event_id) REFERENCES event(event_id) ON DELETE SET NULL
);

-- Create notification_history table (for tracking browser notifications)
CREATE TABLE IF NOT EXISTS notification_history (
    notification_id SERIAL PRIMARY KEY,
    alert_id INTEGER,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alert(alert_id) ON DELETE SET NULL
);

-- Create fcm_tokens table for Firebase Cloud Messaging
CREATE TABLE IF NOT EXISTS fcm_tokens (
    token_id SERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    device_info TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES user_profile(id) ON DELETE CASCADE
);


-- Create a view for pending alerts that need to be shown
CREATE OR REPLACE VIEW pending_alerts_view AS
SELECT a.alert_id, a.title, a.message, a.priority, a.trigger_time 
FROM alert a 
WHERE a.status = 'pending' 
AND a.trigger_time <= NOW() + INTERVAL '30 minutes'
ORDER BY a.priority DESC, a.trigger_time ASC;

-- Create a view for upcoming events
CREATE OR REPLACE VIEW upcoming_events_view AS
SELECT e.event_id, e.event_name, e.start_time, e.end_time, e.location, e.priority
FROM event e
WHERE e.start_time > NOW()
AND e.start_time <= NOW() + INTERVAL '7 days'
ORDER BY e.start_time ASC;

-- Function to clean up old alerts
CREATE OR REPLACE FUNCTION cleanup_old_alerts(days_threshold INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM alert 
    WHERE status = 'sent' 
    AND created_at < NOW() - (days_threshold * INTERVAL '1 day');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_start_time ON chat_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_summaries_session_id ON chat_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_session_id ON recommendation(session_id);
CREATE INDEX IF NOT EXISTS idx_event_start_time ON event(start_time);
CREATE INDEX IF NOT EXISTS idx_activities_start_at ON activities(start_at);
CREATE INDEX IF NOT EXISTS idx_alert_trigger_time ON alert(trigger_time);
CREATE INDEX IF NOT EXISTS idx_activities_tags ON activities USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_activities_analysis_activity_type ON activities_analysis(activity_type);
CREATE INDEX IF NOT EXISTS idx_notification_history_alert_id ON notification_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_user_id ON fcm_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_is_active ON fcm_tokens(is_active);