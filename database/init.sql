-- Create user_profile table (single user)
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    year_of_birth INTEGER,
    address TEXT,
    major VARCHAR(100),
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    content TEXT,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create chat_summaries table
CREATE TABLE chat_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    summarize TEXT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create recommendation table
CREATE TABLE recommendation (
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

-- Create event table
CREATE TABLE event (
    event_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location VARCHAR(100),
    priority VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50)
);

-- Create activities table
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Create alert table
CREATE TABLE alert (
    alert_id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50),
    title VARCHAR(100),
    message TEXT,
    trigger_time TIMESTAMP,
    priority VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create activities_analysis table
CREATE TABLE activities_analysis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    frequency_per_week INTEGER,
    frequency_per_month INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_chat_sessions_start_time ON chat_sessions(start_time);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_chat_summaries_session_id ON chat_summaries(session_id);
CREATE INDEX idx_recommendation_session_id ON recommendation(session_id);
CREATE INDEX idx_event_start_time ON event(start_time);
CREATE INDEX idx_activities_start_at ON activities(start_at);
CREATE INDEX idx_alert_trigger_time ON alert(trigger_time);
CREATE INDEX idx_activities_tags ON activities USING GIN (tags);

-- Insert default user profile (single user setup)
INSERT INTO user_profile (user_name, username, phone_number, year_of_birth, address, major, additional_info)
VALUES ('Default User', 'default_user', NULL, NULL, NULL, NULL, 'Default user profile for single-user chatbot system');