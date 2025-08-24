---
allowed-tools: Bash(sqlite3:*)
description: Get the schema for the table name provided in the arguments
model: claude-sonnet-4-20250514
---

# Using `sqlite3` get the schema of the table name provided in the arguments to this prompt

IMPORTANT INSTRUCTIONS:
- ONLY run the bash command provided
- DO NOT make any edits or changes
- DO NOT create any new files
- DO NOT run any commands
- DO NOT analyze or comment on the contents
- DO NOT read any other files
- After reading the schema do not take any further action

Run this bash command:
```bash
slqite3 data/collect.db ".schema {tablename}"
```

