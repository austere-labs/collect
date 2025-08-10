-- Add github_url column to prompt_history table to track project association in historical records
-- depends: 20250810_01_add-projects-table

-- Add github_url column to prompt_history table
ALTER TABLE prompt_history ADD COLUMN github_url TEXT REFERENCES projects(github_url) ON DELETE SET NULL;

-- Add index for efficient queries by github_url
CREATE INDEX IF NOT EXISTS idx_prompt_history_github_url ON prompt_history(github_url);

-- Down migration (rollback)
-- DROP INDEX IF EXISTS idx_prompt_history_github_url;
-- ALTER TABLE prompt_history DROP COLUMN github_url;