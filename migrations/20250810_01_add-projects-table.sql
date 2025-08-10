-- Add projects table and update prompt table with project reference
-- depends: 20250727_01_create-prompt-tables

-- Projects table creation with github_url as primary key
CREATE TABLE IF NOT EXISTS projects (
    github_url TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add github_url to prompt table
ALTER TABLE prompt ADD COLUMN github_url TEXT REFERENCES projects(github_url) ON DELETE SET NULL;

-- Index for github_url foreign key
CREATE INDEX IF NOT EXISTS idx_prompt_github_url ON prompt(github_url);

-- Down migration (rollback)
-- DROP INDEX IF EXISTS idx_prompt_github_url;
-- ALTER TABLE prompt DROP COLUMN github_url;
-- DROP TABLE IF EXISTS projects;