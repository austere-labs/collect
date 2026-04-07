---
name: claudemd
description: Uses Gemini CLI to analyze the source tree, compares output to existing CLAUDE.md, and writes a CLAUDE_DRAFT.md with proposed improvements. Runs make buildsrc and make tree first, then sends source to Gemini for analysis.
allowed-tools: Bash(uv:*) Bash(make:*) Bash(cat:*) Bash(gemini:*) Bash(rm:*) Read Write
disable-model-invocation: true
---

# Code base summary: Analyze the source and source-tree provided, create a CLAUDE_DRAFT.md output that can be compared to the existing `CLAUDE.md`.

<PRE-WORKFLOW-INSTRUCTIONS>
Run the following bash commands in parallel:

```bash
make buildsrc
```

```bash
make tree
```

```bash
rm -rf CLAUDE_DRAFT.md
```
</PRE-WORKFLOW-INSTRUCTIONS>

<WORKFLOW-INSTRUCTIONS>
Create a todo list with these 4 tasks, then execute them sequentially:
1. Run the provided bash/cli command.
2. Compare and analyze the differences between CLAUDE.md and the output from the first task.
3. Generate proposed changes to CLAUDE.md
4. Write those changes to a CLAUDE_DRAFT.md file and provide a summary
</WORKFLOW-INSTRUCTIONS>

## SEQUENTIAL STEPS:

### STEP 1:
Run this bash command:
```bash
gemini --prompt "Please read provided data here:

<source-directory-structure>
$(cat dir_structure.md)
</source-directory-structure>

<source-code>
$(cat source.md)
</source-code>

**IMPORTANT:** DO NOT under any circumstances try to analyze the current git repository.

Your only job is to analyze the provided data in the prompt which has the entire source tree and source code with supplied xml tags specifying the file, its directory location, a descritpion and its place in the directory structure. Finally then to understand the project structure, technologies, conventions, key files, and architecture.

Focus on identifying:
- Project Overview and purpose
- Complete technology stack
- Key technologies and approaches used
- Languages, libraries and frameworks used
- Building and running instructions, make sure you look at the Makefile for this
- Development conventions
- Architecture details
- Main entry points and core files
- Development commands and workflows
- Database structure and migrations
- Testing approaches,
- Directory organization and purpose of each major component.

IMPORTANT: Do not overwrite the existing CLAUDE.md file or try to create it.

Based on your analysis, output comprehensive CLAUDE.md content in markdown format suitable for Claude Code and the way that Claude Code uses the CLAUDE.md file.
"
```
**IMPORTANT:** When this tool call completes, you should assume it was successful and run `### STEP 2:`

### STEP 2:
- Take the output from `STEP 1` and COMPARE CLAUDE.md to that output and analyze the differences and look for alignment opportunities

### STEP 3:
- Generate proposed changes to CLAUDE.md based on the insights in the output for GEMINI.md
- Identify missing sections, outdated information or improvements needed

### STEP 4:
- WRITE those changes to a file called `CLAUDE_DRAFT.md`
- GENERATE a summary of the changes proposed that exist in `CLAUDE_DRAFT.md`
