# Plan: Add Projects Table and Update Prompt Model

## Overview
Add a new `projects` table to the database and update the `prompt` table to include an optional foreign key reference to projects. This enables tracking which prompts belong to specific projects while maintaining backwards compatibility for prompts without projects.

## Implementation Steps

### 1. Create New Yoyo Migration File
Create a new migration file `migrations/20250810_01_add-projects-table.sql` with proper yoyo format and dependencies.

The migration should:
- Depend on the existing `20250727_01_create-prompt-tables` migration
- Include both up and down migration steps for rollback capability

### 2. Create Projects Table
```sql
-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    github_url TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for github_url for efficient lookups
CREATE INDEX IF NOT EXISTS idx_projects_github_url ON projects(github_url);
```

### 3. Update Prompt Table with Foreign Key
```sql
-- Add project_id column to prompt table (nullable for backwards compatibility)
ALTER TABLE prompt ADD COLUMN project_id TEXT;

-- Add foreign key constraint
ALTER TABLE prompt 
    ADD CONSTRAINT fk_prompt_project 
    FOREIGN KEY (project_id) REFERENCES projects(id)
    ON DELETE SET NULL;

-- Add index for project_id for efficient joins
CREATE INDEX IF NOT EXISTS idx_prompt_project_id ON prompt(project_id);
```

### 4. Migration File Structure
The complete migration file should follow this structure:
```sql
-- Add projects table and update prompt table with project reference
-- depends: 20250727_01_create-prompt-tables

-- Projects table creation
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    github_url TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for github_url
CREATE INDEX IF NOT EXISTS idx_projects_github_url ON projects(github_url);

-- Add project_id to prompt table
ALTER TABLE prompt ADD COLUMN project_id TEXT REFERENCES projects(id) ON DELETE SET NULL;

-- Index for project_id foreign key
CREATE INDEX IF NOT EXISTS idx_prompt_project_id ON prompt(project_id);

-- Down migration (rollback)
-- DROP INDEX IF EXISTS idx_prompt_project_id;
-- ALTER TABLE prompt DROP COLUMN project_id;
-- DROP INDEX IF EXISTS idx_projects_github_url;
-- DROP TABLE IF EXISTS projects;
```

## Key Features
- **Projects table**: Stores project metadata with GitHub URL and description
- **Optional foreign key**: `project_id` in prompt table is nullable for backwards compatibility
- **Referential integrity**: Foreign key constraint ensures valid project references
- **Performance optimization**: Indexes on foreign key and github_url for efficient queries
- **Rollback support**: Down migration steps commented for manual rollback if needed

## Testing Considerations
- Verify existing prompts continue to work without project_id
- Test inserting prompts with valid project_id references
- Verify foreign key constraint prevents invalid project_id values
- Test cascade behavior on project deletion (should set prompt.project_id to NULL)
- Check index performance on joins between prompt and projects tables

## Example Usage
```python
# Create a new project
project = Project(
    id="proj_123",
    github_url="https://github.com/user/repo",
    description="Example project"
)

# Create a prompt linked to the project
prompt_data = PromptData(
    type=PromptType.PLAN,
    status=PromptPlanStatus.DRAFT,
    content="Example prompt content",
    project="Example Project Name"
)

prompt = Prompt(
    id="prompt_456",
    name="example_prompt",
    data=prompt_data,
    project_id="proj_123",  # Links to the project
    version=1,
    content_hash="abc123",
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

## Files to Modify
- [ ] Create `migrations/20250810_01_add-projects-table.sql`
- [✅] Update `repository/prompt_models.py` (already done by user)
  - Added `Project` model
  - Added `project_id: Optional[str]` to `Prompt` model

## Notes
- The Pydantic models have already been updated in `repository/prompt_models.py`
- The migration maintains backwards compatibility by making `project_id` optional
- The `ON DELETE SET NULL` ensures prompts aren't orphaned when projects are deleted
- Consider adding a trigger to update `updated_at` timestamp on projects table modifications