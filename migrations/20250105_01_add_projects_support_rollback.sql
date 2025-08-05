-- Manual rollback script for project support migration
-- For SQLite 3.50.2+ with DROP COLUMN support

-- Drop the view first (depends on prompt table)
DROP VIEW IF EXISTS project_prompts;

-- Drop indexes on prompt table
DROP INDEX IF EXISTS idx_prompt_projects;
DROP INDEX IF EXISTS idx_prompt_is_global;

-- Remove columns from prompt table (SQLite 3.50.2+ supports this)
ALTER TABLE prompt DROP COLUMN projects;
ALTER TABLE prompt DROP COLUMN is_global;

-- Drop the project sync history table
DROP TABLE IF EXISTS project_sync_history;

-- Drop the projects table
DROP TABLE IF EXISTS projects;

-- Verify the rollback
SELECT sql FROM sqlite_master WHERE type='table' AND name='prompt';
SELECT sql FROM sqlite_master WHERE type='table' AND name='projects';