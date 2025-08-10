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
-- Create projects table with github_url as primary key
CREATE TABLE IF NOT EXISTS projects (
    github_url TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Update Prompt Table with Foreign Key
```sql
-- Add github_url column to prompt table (nullable for backwards compatibility)
ALTER TABLE prompt ADD COLUMN github_url TEXT;

-- Add foreign key constraint
ALTER TABLE prompt 
    ADD CONSTRAINT fk_prompt_project 
    FOREIGN KEY (github_url) REFERENCES projects(github_url)
    ON DELETE SET NULL;

-- Add index for github_url for efficient joins
CREATE INDEX IF NOT EXISTS idx_prompt_github_url ON prompt(github_url);
```

### 4. Migration File Structure
The complete migration file should follow this structure:
```sql
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
```

## Key Features
- **Projects table**: Stores project metadata with GitHub URL as primary key and description
- **Optional foreign key**: `github_url` in prompt table is nullable for backwards compatibility
- **Referential integrity**: Foreign key constraint ensures valid project references
- **Performance optimization**: Index on github_url foreign key for efficient queries
- **Rollback support**: Down migration steps commented for manual rollback if needed

## Testing Considerations
- Verify existing prompts continue to work without project_id
- Test inserting prompts with valid project_id references
- Verify foreign key constraint prevents invalid github_url values
- Test cascade behavior on project deletion (should set prompt.github_url to NULL)
- Check index performance on joins between prompt and projects tables

## Example Usage
```python
# Create a new project
project = Project(
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
    github_url="https://github.com/user/repo",  # Links to the project
    version=1,
    content_hash="abc123",
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

## Files to Modify
- [ ] Create `migrations/20250810_01_add-projects-table.sql`
- [✅] Update `repository/prompt_models.py` (already done by user)
  - Added `Project` model with `github_url` as primary identifier
  - Added `github_url: Optional[str]` to `Prompt` model

## Notes
- The Pydantic models have already been updated in `repository/prompt_models.py`
- The migration maintains backwards compatibility by making `github_url` optional
- The `ON DELETE SET NULL` ensures prompts aren't orphaned when projects are deleted
- Using `github_url` as primary key eliminates the need for a separate `id` field
- Consider adding a trigger to update `updated_at` timestamp on projects table modifications
