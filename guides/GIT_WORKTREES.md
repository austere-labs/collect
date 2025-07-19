# Git Worktrees Quick Reference

Git worktrees allow you to have multiple working directories for a single repository, enabling you to work on different branches simultaneously without stashing or committing.

## Why Use Worktrees?

- Work on multiple branches without switching
- Keep separate builds/dependencies per branch
- Review PRs while working on features
- Avoid losing uncommitted work when switching branches

## Essential Commands

### Create a Worktree

```bash
# Create worktree for existing branch
git worktree add ../project-feature feature-branch

# Create worktree with new branch
git worktree add -b new-feature ../project-new-feature

# Create worktree from specific commit
git worktree add ../project-fix HEAD~3
```

### List Worktrees

```bash
git worktree list
# Shows all worktrees with their paths and branches
```

### Remove a Worktree

```bash
# Remove worktree (after deleting directory)
rm -rf ../project-feature
git worktree prune

# Force remove worktree
git worktree remove ../project-feature
```

## Common Workflows

### 1. Feature Development
```bash
# Create worktree for new feature
git worktree add -b feature/auth ../myapp-auth

# Work in the new directory
cd ../myapp-auth
# Make changes, commit, push
```

### 2. Hotfix While Working
```bash
# Working on feature, need to fix production
git worktree add -b hotfix/critical ../myapp-hotfix origin/main

# Fix issue in hotfix worktree
cd ../myapp-hotfix
# Fix, test, commit, push, create PR

# Return to feature work
cd ../myapp-feature
```

### 3. PR Review
```bash
# Review a colleague's PR
git fetch origin
git worktree add ../myapp-review origin/pr/123

# Test and review
cd ../myapp-review
# Run tests, review code
```

## Best Practices

1. **Naming Convention**: Use descriptive directory names
   ```bash
   git worktree add ../project-feature-auth feature/auth
   git worktree add ../project-fix-bug-123 bugfix/issue-123
   ```

2. **Clean Up**: Remove worktrees when done
   ```bash
   git worktree list
   git worktree remove ../project-old-feature
   ```

3. **Avoid Shared Branches**: Don't check out the same branch in multiple worktrees

4. **Directory Organization**: Keep worktrees in a parent directory
   ```
   myproject/
   ├── main/          (main worktree)
   ├── feature-auth/  (worktree)
   ├── hotfix-123/    (worktree)
   └── review-pr456/  (worktree)
   ```

## Quick Tips

- Worktrees share the same `.git` directory (saves space)
- Each worktree has its own working directory and index
- Perfect for CI/CD scenarios with different build configurations
- Use `git worktree lock` to prevent accidental removal

## Example: Complete Feature Workflow

```bash
# 1. Create feature worktree
git worktree add -b feature/payment ../myapp-payment

# 2. Develop feature
cd ../myapp-payment
# ... make changes ...
git add .
git commit -m "feat: add payment processing"
git push -u origin feature/payment

# 3. Create PR
gh pr create

# 4. After PR merged, cleanup
cd ../myapp
git worktree remove ../myapp-payment
```