-- Create user_profile table
CREATE TABLE user_profile (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20),
    year_of_birth INTEGER,
    address TEXT,
    major VARCHAR(100),
    additional_info TEXT
);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
);

-- Create chat_messages table
CREATE TABLE chat_messages (
    message_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    content TEXT,
    looker_user VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create chat_summaries table
CREATE TABLE chat_summaries (
    session_id INTEGER PRIMARY KEY, 
    summarize TEXT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create recommendation table (FIXED)
CREATE TABLE recommendation (
    recommendation_id SERIAL PRIMARY KEY,
    session_id INTEGER,
    recommendation_type VARCHAR(50),
    title VARCHAR(100),
    content TEXT,
    score FLOAT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_at TIMESTAMP,
    status VARCHAR(20),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE SET NULL

-- Create event table
CREATE TABLE event (
    event_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location VARCHAR(100),
    priority VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
);

-- Create activities table (FIXED array syntax)
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
);

-- Create alert table
CREATE TABLE alert (
    alert_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    alert_type VARCHAR(50),
    title VARCHAR(100),
    message TEXT,
    trigger_time TIMESTAMP,
    priority VARCHAR(20),
    status VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
);

-- Create activities_analysis table
CREATE TABLE activities_analysis (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100),
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    frequency_per_week INTEGER,
    frequency_per_month INTEGER,
    FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_start_time ON chat_sessions(start_time);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_event_user_id ON event(user_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_alert_user_id ON alert(user_id);
CREATE INDEX idx_activities_analysis_user_id ON activities_analysis(user_id);
CREATE INDEX idx_activities_tags ON activities USING GIN (tags);