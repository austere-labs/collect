---
allowed-tools: Bash(git status:*), Bash(git add:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*)
description: Commit all changes 
model: sonnet
---

# Git Commit: Auto-stage and Commit Changes

## Context:
You are acting as a Senior Software Engineer performing a git commit. This command automatically stages all changes and creates a commit with a well-crafted message.

## Workflow Steps:

### Step 1: Check Repository Status
Run `git status` to check for unstaged changes.

### Step 2: Stage Changes (if needed)
If there are unstaged changes:
- Run `git add .` to stage all changes
- Inform the user that all changes have been staged

### Step 3: Analyze Changes
Run these commands in parallel to understand what's being committed:
- `git status` - Verify all changes are staged
- `git diff --staged` - Review the actual changes being committed
- `git log --oneline -3` - Check recent commits for context and style

### Step 4: Create Commit Message
Based on the staged changes, craft a clear and succinct commit message:
- Use conventional commit format when appropriate (feat:, fix:, docs:, refactor:, test:, chore:)
- Keep the first line under 72 characters
- Include a brief but descriptive summary of what changed
- Focus on the "what" and "why" rather than the "how"

Format:
```
type(scope): brief description of changes

Additional details if necessary (optional)
- Key change 1
- Key change 2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Step 5: Commit Changes
Execute the commit using:
```bash
git commit -m "$(cat <<'EOF'
[Your crafted commit message here]

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 6: Verify Success
- Confirm the commit was created successfully
- Show the user the commit hash and message
- Run `git status` to confirm working directory is clean

## Important Notes:
- This command stages ALL changes with `git add .`
- Review changes carefully before committing
- The commit will include the Claude Code attribution
- Does NOT push to remote (user must run `git push` separately if desired)

## Example Output:
```
Checking repository status...
Found unstaged changes. Staging all files...
All changes staged successfully.

Analyzing changes...
Creating commit with message:
"fix(prompt_service): add support for .toml file extensions

Updated normalize_filename to preserve .toml extensions
- Modified function to check for both .md and .toml
- Updated docstrings to reflect dual extension support

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

Commit created successfully: abc1234
Working directory is now clean.
```
