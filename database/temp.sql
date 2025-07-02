ALTER TABLE event ADD COLUMN embedding vector(1536);
CREATE EXTENSION IF NOT EXISTS vector;

-- Add status column to activities table
ALTER TABLE activities 
ADD COLUMN status VARCHAR(20) DEFAULT 'pending';

-- Add index for better performance
CREATE INDEX idx_activities_status ON activities(status);

-- Update existing records to 'pending'
UPDATE activities SET status = 'pending' WHERE status IS NULL;