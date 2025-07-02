# Git Worktrees Guide

Git worktrees allow you to have multiple branches checked out simultaneously in different directories. This is incredibly useful when you need to work on multiple features, review PRs, or quickly switch contexts without stashing changes.

## What are Git Worktrees?

A git worktree is a linked working tree that shares the same repository but allows you to have different branches checked out in different directories. All worktrees share:
- The same `.git` directory (repository data)
- The same remote configurations
- The same stash entries
- The same commit history

## Creating a Worktree

### Basic Syntax
```bash
git worktree add <path> <branch>
```

### Examples

#### Create worktree from existing branch
```bash
# Create a worktree for the 'feature/auth' branch in a new directory
git worktree add ../myproject-auth feature/auth

# Create worktree in a specific location
git worktree add /tmp/hotfix hotfix/urgent-bug
```

#### Create worktree with a new branch
```bash
# Create a new branch and worktree simultaneously
git worktree add -b feature/new-ui ../myproject-new-ui

# Create from a specific commit or tag
git worktree add -b release/v2.0 ../myproject-v2 v2.0-tag
```

#### Practical Example
```bash
# You're working on main in /Users/you/myproject
cd /Users/you/myproject

# Create a worktree for a new feature
git worktree add -b feature/payment-integration ../myproject-payments

# Now you have:
# /Users/you/myproject (main branch)
# /Users/you/myproject-payments (feature/payment-integration branch)

# Navigate to the new worktree
cd ../myproject-payments

# Work on your feature
echo "Payment module" > payment.py
git add payment.py
git commit -m "Add payment module"
```

## Working with Worktrees

### List all worktrees
```bash
git worktree list
# Output:
# /Users/you/myproject         abc1234 [main]
# /Users/you/myproject-payments def5678 [feature/payment-integration]
```

### Switch between worktrees
Simply use `cd` to navigate between directories:
```bash
cd /Users/you/myproject          # main branch
cd /Users/you/myproject-payments  # feature branch
```

## Merging Worktree Changes Back to Main

Since worktrees share the same repository, merging is straightforward:

### Step 1: Commit changes in your worktree
```bash
cd /Users/you/myproject-payments
git add .
git commit -m "Complete payment integration"
git push -u origin feature/payment-integration
```

### Step 2: Switch to main (in any worktree or main directory)
```bash
cd /Users/you/myproject  # Or stay in any worktree
git checkout main
git pull origin main     # Ensure main is up to date
```

### Step 3: Merge the feature branch
```bash
# Simple merge
git merge feature/payment-integration

# Or merge with a merge commit (recommended for features)
git merge --no-ff feature/payment-integration

# Or rebase if you prefer linear history
git rebase main feature/payment-integration
```

### Step 4: Push to remote
```bash
git push origin main
```

### Step 5: Clean up (optional)
```bash
# Delete the local branch
git branch -d feature/payment-integration

# Delete the remote branch
git push origin --delete feature/payment-integration

# Remove the worktree
git worktree remove /Users/you/myproject-payments
```

## Alternative: Using Pull Requests

For team workflows, you might prefer Pull Requests:

```bash
# 1. In your worktree, push the branch
cd /Users/you/myproject-payments
git push -u origin feature/payment-integration

# 2. Create PR via GitHub/GitLab/Bitbucket web interface

# 3. After PR is merged, clean up locally
git worktree remove /Users/you/myproject-payments
git branch -d feature/payment-integration
```

## Worktree Management

### Remove a worktree
```bash
# Remove worktree (must be clean with no uncommitted changes)
git worktree remove /path/to/worktree

# Force removal (discards local changes)
git worktree remove --force /path/to/worktree
```

### Prune stale worktrees
```bash
# Remove worktree references if directory was deleted manually
git worktree prune
```

### Lock/unlock a worktree
```bash
# Prevent a worktree from being pruned
git worktree lock /path/to/worktree

# Unlock it later
git worktree unlock /path/to/worktree
```

## Best Practices

1. **Use descriptive paths**: Name worktree directories after their purpose
   ```bash
   git worktree add ../project-bugfix-auth bugfix/auth-issue
   git worktree add ../project-feature-api feature/new-api
   ```

2. **Keep worktrees organized**: Use a consistent structure
   ```bash
   ~/work/
     myproject/          # main
     myproject-feature1/ # feature branch
     myproject-hotfix/   # hotfix branch
   ```

3. **Clean up regularly**: Remove worktrees when done
   ```bash
   git worktree list
   git worktree remove <path>
   ```

4. **Don't share worktree directories**: Each developer should create their own

5. **Commit before switching**: Although you can leave changes uncommitted, it's cleaner to commit or stash first

## Common Issues and Solutions

### "fatal: '<branch>' is already checked out at '<path>'"
You can't have the same branch checked out in multiple worktrees. Either:
- Use the existing worktree: `cd <path>`
- Or checkout a different branch in one of the worktrees

### Worktree directory was manually deleted
```bash
git worktree prune  # Cleans up references to missing worktrees
```

### Need to move a worktree
```bash
git worktree move <old-path> <new-path>
```

## Quick Reference

```bash
# Create worktree
git worktree add <path> <branch>
git worktree add -b <new-branch> <path>

# List worktrees
git worktree list

# Remove worktree
git worktree remove <path>

# Clean up stale entries
git worktree prune

# Move worktree
git worktree move <old> <new>

# Lock/unlock
git worktree lock <path>
git worktree unlock <path>
```

## Example Workflow

Here's a complete example of using worktrees for feature development:

```bash
# Starting in main project directory
cd ~/projects/myapp

# 1. Create a worktree for a new feature
git worktree add -b feature/user-profiles ../myapp-profiles

# 2. Work on the feature
cd ../myapp-profiles
# ... make changes ...
git add .
git commit -m "Add user profile functionality"
git push -u origin feature/user-profiles

# 3. Switch back to main for a hotfix
cd ../myapp
git pull origin main
# ... fix critical bug ...
git add .
git commit -m "Fix critical auth bug"
git push origin main

# 4. Continue feature work without any stashing needed
cd ../myapp-profiles
# ... complete feature ...
git add .
git commit -m "Complete user profiles"
git push

# 5. Merge feature to main
cd ../myapp
git checkout main
git pull origin main
git merge --no-ff feature/user-profiles
git push origin main

# 6. Clean up
git branch -d feature/user-profiles
git push origin --delete feature/user-profiles
git worktree remove ../myapp-profiles

# Verify cleanup
git worktree list  # Should only show main worktree
```

This workflow demonstrates the power of worktrees: you can quickly switch between feature development and hotfixes without the overhead of stashing, checking out different branches, and potentially losing context.