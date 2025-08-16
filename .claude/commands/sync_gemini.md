---
allowed-tools: Bash(cat:*), Bash(gemini:*), TodoWrite, Read, Write
description: Analyze code base with gemini and sync *.md files
model: claude-sonnet-4-20250514
---

## WORKFLOW INSTRUCTIONS:
**Use TodoWrite tool to create a todo list with these 4 tasks, then execute them sequentially:**
1. Run the provided bash/cli command. This will create a new GEMINI.md file
2. Compare and analyze the differences between CLAUDE.md and GEMINI.md 
3. Generate proposed changes to CLAUDE.md
4. Write those changes to a CLAUDE_DRAFT.md file and provide a summary

### SEQUENTIAL STEPS:

#### STEP 1:
Run this bash command:
```bash
gemini --prompt "Please read provided data here:

<source-directory-structure>
$(cat dir_structure.md)
<source-directory-structure>

<source code>
$(cat source.md)
</source code>

**IMPORTANT:** DO NOT under any circumstances try to analyze the current git repository.

Your only job is to analyze the provided data in the prompt which provides the entire source tree and source code with supplied xml tags specifying the file and its directory structure and then understand the project structure, technologies, conventions, key files, and architecture. 
Focus on identifying: 
- Project Overview and purpose
- Complete technology stack
- Key technologies used
- Languages, libraries and frameworks used
- Building and running instructions, make sure you look at the Makefile for this
- Development conventions
- Architecture details
- Main entry points and core files
- Development commands and workflows
- Database structure and migrations
- Testing approaches, 
- Directory organization and purpose of each major component.

IMPORTANT: Do not overwrite the existing GEMINI.md file or try to create it.

Based on your analysis, output comprehensive GEMINI.md content in markdown format suitable for the Gemini Code Assistant context.
"
```
**IMPORTANT:** When this tool call completes, you should assume it was successful and run `#### STEP 2:`

#### STEP 2:
- Take the output from `STEP 1` and COMPARE CLAUDE.md to that output andand analyze the differences and look for alignment opportunities

#### STEP 3:
- Generate proposed changes to CLAUDE.md based on the insights in GEMINI.md
- Identify missing sections, outdated information or improvements needed

#### STEP 4:
- WRITE those changes to a file called `CLAUDE_DRAFT.md`
- IF the `CLAUDE_DRAFT.md` file already exists THEN Delete it by running the following bash command:

```bash
rm CLAUDE_DRAFT.md
```
- GENERATE a summary of the changes proposed that exist in `CLAUDE_DRAFT.md`
