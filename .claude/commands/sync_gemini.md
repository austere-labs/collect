---
allowed-tools: Bash(cat:*), Bash(gemini:*)
description: Analyze code base with gemini and sync *.md files
model: claude-sonnet-4-20250514
---

## WORKFLOW INSTRUCTIONS:
1. Run the provided bash/cli command. This will create a new GEMINI.md file
2. Compare and analyze the differences between CLAUDE.md and GEMINI.md 
3. Generate proposed changes to CLAUDE.md
4. Write those changes to a CLAUDE_DRAFT.md file and provide a summary

### SEQUENTIAL STEPS:

#### STEP 1:
Run this bash command:
```bash
cat source.md | gemini --prompt "Please read provided source code:
Understand the project structure, technologies, conventions, key files, and architecture. 
Focus on identifying: 
- Project Overview and purpose
- Complete technology stack
- Building and running instructions
- Development conventions
- Architecture details
- Main entry points and core files
- Key technologies, libraries and frameworks used
- Development commands and workflows
- Database structure and migrations
- Testing approaches, 
- Directory organization and purpose of each major component.

Based on your analysis, please provide a comprehensive new version of GEMINI.md inmarkdown format that is suitable for the Gemini Code Assistant context

Please write this file to the current directory and call it GEMINI.md. If the file exists, please overwrite it.
"
```

#### STEP 2:
- COMPARE CLAUDE.md to GEMINI.md and analyze the differences and look for alignment opportunities

#### STEP 3:
- Generate proposed changes to CLAUDE.md based on the insights in GEMINI.md
- Identify missing sections, outdated information or improvements needed

#### STEP 4:
- WRITE those changes to a file called `CLAUDE_DRAFT.md`
- GENERATE a summary of the changes proposed that exist in `CLAUDE_DRAFT.md`
