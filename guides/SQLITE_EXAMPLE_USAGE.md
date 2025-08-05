## Example Usage for VIEW: project_prompts


```sql
-- Find all global prompts
SELECT * FROM project_prompts WHERE scope = 'global';

-- Find prompts for a specific project
SELECT * FROM project_prompts 
WHERE scope = 'project-specific' 
AND json_extract(projects, '$') LIKE '%"my-project"%';

-- Find orphaned prompts
SELECT * FROM project_prompts WHERE scope = 'unassigned';

-- Count prompts by scope
SELECT scope, COUNT(*) as count 
FROM project_prompts 
GROUP BY scope;
```
