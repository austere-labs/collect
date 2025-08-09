# Git Workflow: Staged Changes Commit and Pull Request Creation

## Context:
You are acting as a Senior Principal Software Engineer reviewing staged code changes. Analyze only the staged modifications and take appropriate git actions based on the current repository state and branch configuration.

**IMPORTANT: This command only works with staged changes. If no changes are staged, inform the user to stage their changes first.**

**IMPORTANT: If we are on the main branch DO NOT create a branch and do try to create a pr.**

## Workflow Steps:

### Step 1: Repository State Analysis
Run these commands in parallel to understand the current state:
- `git status` - Check working tree status and current branch
- `git diff --staged` - Analyze staged changes (PRIMARY FOCUS)
- `git log --oneline -5` - Review recent commit history for context
- `git branch -a` - List all branches to understand branching strategy

**Exit early if no staged changes are found** - inform user to run `git add <files>` first.

### Step 2: Staged Changes Analysis
Perform thorough analysis of **only the staged changes**:
- **Scope**: Identify staged files modified, added, or deleted
- **Purpose**: Determine if staged changes represent new features, bug fixes, refactoring, or documentation updates
- **Impact**: Assess potential effects on existing functionality from staged changes only
- **Quality**: Check staged code for style consistency and best practices
- **Security**: Identify any potential security implications in staged changes

### Step 3: Decision Logic
Based on your analysis of staged changes, choose the appropriate action:

#### Option A: Direct Commit (when on main/master branch)
If working directly on the main branch with staged changes:
1. Create a comprehensive commit message following conventional commit format:
   ```
   type(scope): brief description
   
   Detailed explanation of what and why
   - Specific change 1
   - Specific change 2
   
   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
2. Commit the staged changes with `git commit`
3. Push changes with `git push`

#### Option B: Pull Request Creation (when on feature branch)
If on a feature branch:
1. Commit the staged changes with a clear commit message
2. Push branch to remote with `git push -u origin <branch-name>` if needed
3. Create PR with structured format based on the staged changes and capture the PR URL:

```bash
gh pr create --title "Clear, actionable title describing the change" --body "$(cat <<'EOF'
## Summary
- Concise bullet points explaining what was changed and why
- Focus on business value and technical impact

## Changes Made
- Specific technical changes implemented
- New features or functionality added
- Bug fixes or improvements

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases considered

## Notes
- Any deployment considerations
- Breaking changes (if any)
- Follow-up tasks needed

🤖 Generated with Claude Code
EOF
)"
```
4. **IMPORTANT** Please copy the url of the pull request to my clipboard:

```bash
echo {url} | pbcopy
```

### Step 4: Quality Assurance
After taking action:
- Verify the commit/PR was created successfully
- Confirm all staged changes are included in the commit
- Check that commit messages accurately reflect the staged changes
- Ensure branch protection rules are respected
- **If a PR was created**: Use the `copy_clipboard` MCP tool to copy the PR URL to clipboard for easy sharing

## Best Practices:
- **Staged Changes Only**: Never include unstaged changes in commits
- **Commit Messages**: Use conventional commit format (feat:, fix:, docs:, etc.) based on staged changes
- **PR Titles**: Start with action verb, be specific about staged changes
- **PR Bodies**: Include context and testing notes for staged modifications only
- **Scope**: Ensure staged changes are focused and atomic
- **Pre-commit Checks**: Verify staged changes pass linting and tests before committing

## Examples:

**Good Commit Message (based on staged changes):**
```
feat(api): add user authentication middleware

Implements JWT-based authentication for protected routes
- Add middleware for token validation (staged in auth/middleware.py)
- Update user routes to require authentication (staged in routes/users.py)
- Add error handling for invalid tokens (staged in utils/errors.py)

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Good PR Title & Body (based on staged changes):**
```bash
gh pr create --title "Add user authentication middleware to API endpoints" --body "$(cat <<'EOF'
## Summary  
- Implements JWT-based authentication system for API security
- Adds middleware layer for token validation on protected routes

## Changes Made (Staged)
- Created authentication middleware with JWT validation (auth/middleware.py)
- Updated user routes to require authentication (routes/users.py)  
- Added comprehensive error handling for invalid/expired tokens (utils/errors.py)
- Updated API documentation with authentication requirements (docs/api.md)

## Testing
- [x] Unit tests for middleware functionality
- [x] Integration tests for protected routes
- [x] Manual testing with valid/invalid tokens
- [x] Edge cases: expired tokens, malformed tokens

## Note
All changes have been staged and are ready for review. No unstaged modifications included.

🤖 Generated with Claude Code
EOF
)"
```

## Pre-Flight Checklist:
Before running this command, ensure:
- [ ] Your intended changes are staged with `git add <files>`
- [ ] You have reviewed staged changes with `git diff --staged`
- [ ] Staged changes are complete and ready for commit
- [ ] No additional unstaged changes should be included
