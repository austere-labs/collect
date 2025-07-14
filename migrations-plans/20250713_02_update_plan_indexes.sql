-- Update plan indexes to match plan_models.py structure
-- depends: 20250713_01_create_plans_tables

-- Drop the incorrect index
DROP INDEX IF EXISTS idx_plan_type;

-- Add indexes that match the PlanData model structure
CREATE INDEX idx_plan_tags ON plans(data ->> '$.tags');
CREATE INDEX idx_plan_description ON plans(data ->> '$.description');

-- Add index for markdown content search (for full-text search if needed)
-- Note: SQLite FTS would be better for full markdown search, but this helps with basic queries
CREATE INDEX idx_plan_content_length ON plans(length(data ->> '$.markdown_content'));