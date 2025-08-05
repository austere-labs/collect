```python
import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('data/collect.db')
cursor = conn.cursor()

# Example 1: Set projects for a specific prompt
prompt_id = "some-prompt-id"
project_names = ["project1", "project2", "project3"]

cursor.execute("""
    UPDATE prompt 
    SET projects = json(?),
        updated_at = datetime('now')
    WHERE id = ?
""", (json.dumps(project_names), prompt_id))

# Example 2: Add a project to existing projects
prompt_id = "some-prompt-id"
new_project = "new-project"

cursor.execute("""
    UPDATE prompt 
    SET projects = json_insert(projects, '$[#]', ?),
        updated_at = datetime('now')
    WHERE id = ?
""", (new_project, prompt_id))

# Example 3: Remove a project from the array
prompt_id = "some-prompt-id"
project_to_remove = "project2"

cursor.execute("""
    UPDATE prompt 
    SET projects = json_remove(projects, 
        '$[' || (
            SELECT key 
            FROM json_each(projects) 
            WHERE value = ?
        ) || ']'
    ),
    updated_at = datetime('now')
    WHERE id = ?
""", (project_to_remove, prompt_id))

# Example 4: Replace entire projects array using Python manipulation
prompt_id = "some-prompt-id"

# First, get current projects
cursor.execute("SELECT projects FROM prompt WHERE id = ?", (prompt_id,))
current_projects = json.loads(cursor.fetchone()[0])

# Modify in Python
current_projects.append("another-project")
current_projects = list(set(current_projects))  # Remove duplicates

# Update back
cursor.execute("""
    UPDATE prompt 
    SET projects = json(?),
        updated_at = datetime('now')
    WHERE id = ?
""", (json.dumps(current_projects), prompt_id))

# Example 5: Bulk update - mark prompts as global
cursor.execute("""
    UPDATE prompt 
    SET is_global = 1,
        projects = '[]',
        updated_at = datetime('now')
    WHERE json_extract(data, '$.type') = 'cmd'
""")

# Example 6: Assign multiple prompts to a project
project_name = "my-new-project"
prompt_ids = ["id1", "id2", "id3"]

for prompt_id in prompt_ids:
    cursor.execute("""
        UPDATE prompt 
        SET projects = json_array(?),
            updated_at = datetime('now')
        WHERE id = ?
    """, (project_name, prompt_id))

# Don't forget to commit!
conn.commit()
conn.close()
```

## Using with PromptService class
You could also add methods to your PromptService:

```python
class PromptService:
    def assign_prompt_to_projects(self, prompt_id: str, project_names: List[str]):
        """Assign a prompt to specific projects"""
        self.conn.execute("""
            UPDATE prompt 
            SET projects = json(?),
                updated_at = datetime('now')
            WHERE id = ?
        """, (json.dumps(project_names), prompt_id))
        self.conn.commit()
    
    def add_project_to_prompt(self, prompt_id: str, project_name: str):
        """Add a project to a prompt's project list"""
        # Get current projects
        cursor = self.conn.execute(
            "SELECT projects FROM prompt WHERE id = ?", 
            (prompt_id,)
        )
        row = cursor.fetchone()
        if row:
            current_projects = json.loads(row[0])
            if project_name not in current_projects:
                current_projects.append(project_name)
                self.assign_prompt_to_projects(prompt_id, current_projects)
    
    def mark_prompt_as_global(self, prompt_id: str):
        """Mark a prompt as global (available to all projects)"""
        self.conn.execute("""
            UPDATE prompt 
            SET is_global = 1,
                projects = '[]',
                updated_at = datetime('now')
            WHERE id = ?
        """, (prompt_id,))
        self.conn.commit()
```

The key points:
- Use `json(?)` or `json_array(?)` SQL functions to ensure proper JSON formatting
- Always update `updated_at` timestamp when modifying
- Use `json.dumps()` in Python to convert lists to JSON strings
- Use `json.loads()` to convert JSON strings back to Python lists
