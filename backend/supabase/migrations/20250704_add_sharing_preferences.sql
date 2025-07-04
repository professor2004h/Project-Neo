BEGIN;

-- Add sharing_preferences column to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS sharing_preferences JSONB DEFAULT '{"include_knowledge_bases": true, "include_custom_mcp_tools": true}';

-- Add index for sharing_preferences queries (optional but helpful for performance)
CREATE INDEX IF NOT EXISTS idx_agents_sharing_preferences ON agents USING gin(sharing_preferences);

-- Update existing agents to have default sharing preferences
UPDATE agents 
SET sharing_preferences = '{"include_knowledge_bases": true, "include_custom_mcp_tools": true}'
WHERE sharing_preferences IS NULL;

COMMIT; 