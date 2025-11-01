---
allowed-tools: Bash(sqlite3:*)
description: Lists all plans in the database
model: claude-sonnet-4-5-20250929
---

Run this bash command:
```bash
sqlite3 data/collect.db "SELECT name FROM prompt WHERE data ->> '\$.type' = 'plan'
```

Please print them out nicely so they are readable with a little bit of color.
