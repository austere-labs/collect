"""
Add projects table and multi-project support to prompts

from yoyo import step

__depends__ = {}
"""

from yoyo import step

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS projects (
            name TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            description TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_synced_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            config JSONB DEFAULT '{}'
        )
        """,
        "DROP TABLE IF EXISTS projects"
    ),
    
    step(
        """
        CREATE INDEX idx_projects_registered_at ON projects(registered_at);
        """,
        "DROP INDEX IF EXISTS idx_projects_registered_at"
    ),
    
    step(
        """
        CREATE INDEX idx_projects_is_active ON projects(is_active);
        """,
        "DROP INDEX IF EXISTS idx_projects_is_active"
    ),
    
    # Add projects column to prompt table as JSONB array
    step(
        """
        ALTER TABLE prompt ADD COLUMN projects JSONB DEFAULT '[]';
        """,
        """
        ALTER TABLE prompt DROP COLUMN projects;
        """
    ),
    
    # Add is_global flag for prompts that apply to all projects
    step(
        """
        ALTER TABLE prompt ADD COLUMN is_global BOOLEAN DEFAULT 0;
        """,
        """
        ALTER TABLE prompt DROP COLUMN is_global;
        """
    ),
    
    # Create index for efficient project filtering
    step(
        """
        CREATE INDEX idx_prompt_projects ON prompt(projects);
        """,
        "DROP INDEX IF EXISTS idx_prompt_projects"
    ),
    
    step(
        """
        CREATE INDEX idx_prompt_is_global ON prompt(is_global);
        """,
        "DROP INDEX IF EXISTS idx_prompt_is_global"
    ),
    
    # Create a project_prompts view for easier querying
    step(
        """
        CREATE VIEW project_prompts AS
        SELECT 
            p.*,
            CASE 
                WHEN p.is_global = 1 THEN 'global'
                WHEN json_array_length(p.projects) = 0 THEN 'unassigned'
                ELSE 'project-specific'
            END as scope
        FROM prompt p;
        """,
        "DROP VIEW IF EXISTS project_prompts"
    ),
    
    # Add project sync history table
    step(
        """
        CREATE TABLE IF NOT EXISTS project_sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            sync_type TEXT NOT NULL CHECK(sync_type IN ('full', 'incremental', 'selective')),
            prompts_synced INTEGER DEFAULT 0,
            directories_created INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT CHECK(status IN ('running', 'completed', 'failed')),
            error_message TEXT,
            FOREIGN KEY (project_name) REFERENCES projects(name) ON DELETE CASCADE
        )
        """,
        "DROP TABLE IF EXISTS project_sync_history"
    ),
    
    step(
        """
        CREATE INDEX idx_sync_history_project ON project_sync_history(project_name);
        """,
        "DROP INDEX IF EXISTS idx_sync_history_project"
    ),
    
    step(
        """
        CREATE INDEX idx_sync_history_started ON project_sync_history(started_at);
        """,
        "DROP INDEX IF EXISTS idx_sync_history_started"
    ),
    
    # Migrate existing prompts - mark commands as global by default
    step(
        """
        UPDATE prompt 
        SET is_global = 1 
        WHERE json_extract(data, '$.type') = 'cmd';
        """,
        """
        UPDATE prompt 
        SET is_global = 0 
        WHERE json_extract(data, '$.type') = 'cmd';
        """
    ),
    
    # Migrate existing plan prompts - assign to their project
    step(
        """
        UPDATE prompt 
        SET projects = json_array(json_extract(data, '$.project'))
        WHERE json_extract(data, '$.type') = 'plan' 
        AND json_extract(data, '$.project') IS NOT NULL;
        """,
        """
        UPDATE prompt 
        SET projects = '[]'
        WHERE json_extract(data, '$.type') = 'plan';
        """
    )
]