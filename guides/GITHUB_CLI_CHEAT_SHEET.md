# GitHub CLI (gh) Cheat Sheet

The GitHub CLI brings GitHub functionality directly to your terminal. Install with `brew install gh` or visit [cli.github.com](https://cli.github.com).

## Authentication

```bash
gh auth login                          # Interactive login
gh auth login --with-token < token.txt # Login with personal access token
gh auth logout                         # Logout
gh auth status                         # Check authentication status
gh auth refresh                        # Refresh authentication
gh auth setup-git                      # Configure Git to use gh as credential helper
```

## Repository Management

### Creating & Cloning
```bash
gh repo create myrepo                  # Create repo (interactive)
gh repo create myrepo --private        # Create private repo
gh repo create myrepo --clone          # Create and clone
gh repo clone owner/repo               # Clone repository
gh repo fork owner/repo                # Fork repository
gh repo fork owner/repo --clone        # Fork and clone
```

### Repository Operations
```bash
gh repo list                           # List your repositories
gh repo list owner                     # List user's repositories
gh repo view                           # View current repo details
gh repo view owner/repo                # View specific repo
gh repo delete owner/repo              # Delete repository
gh repo rename new-name                # Rename current repo
gh repo sync                           # Sync fork with upstream
```

## Pull Requests

### Creating & Managing
```bash
gh pr create                           # Create PR (interactive)
gh pr create --title "Title" --body "Description"
gh pr create --draft                   # Create draft PR
gh pr create --assignee @me            # Assign to yourself
gh pr create --label bug,feature       # Add labels
```

### Viewing & Listing
```bash
gh pr list                             # List PRs
gh pr list --state closed             # List closed PRs
gh pr list --author @me                # List your PRs
gh pr view 123                         # View PR details
gh pr view 123 --web                   # Open PR in browser
gh pr diff 123                         # View PR diff
```

### PR Operations
```bash
gh pr checkout 123                     # Checkout PR branch
gh pr merge 123                        # Merge PR
gh pr merge 123 --squash               # Squash merge
gh pr close 123                        # Close PR
gh pr reopen 123                       # Reopen PR
gh pr ready 123                        # Mark draft as ready
gh pr review 123 --approve             # Approve PR
gh pr review 123 --request-changes     # Request changes
```

## Issues

### Creating & Managing
```bash
gh issue create                        # Create issue (interactive)
gh issue create --title "Bug report" --body "Description"
gh issue create --label bug --assignee @me
gh issue edit 123                      # Edit issue
gh issue close 123                     # Close issue
gh issue reopen 123                    # Reopen issue
```

### Viewing & Listing
```bash
gh issue list                          # List issues
gh issue list --state closed          # List closed issues
gh issue list --assignee @me          # List your assigned issues
gh issue list --label bug             # Filter by label
gh issue view 123                      # View issue details
gh issue view 123 --web               # Open issue in browser
```

### Issue Operations
```bash
gh issue comment 123 --body "Comment" # Add comment
gh issue pin 123                       # Pin issue
gh issue unpin 123                     # Unpin issue
gh issue transfer 123 owner/repo      # Transfer issue
```

## GitHub Actions

### Workflows
```bash
gh workflow list                       # List workflows
gh workflow view workflow.yml          # View workflow details
gh workflow run workflow.yml           # Trigger workflow
gh workflow enable workflow.yml        # Enable workflow
gh workflow disable workflow.yml       # Disable workflow
```

### Workflow Runs
```bash
gh run list                            # List workflow runs
gh run list --workflow=ci.yml          # Filter by workflow
gh run view 123456                     # View run details
gh run watch 123456                    # Watch run in real-time
gh run cancel 123456                   # Cancel run
gh run rerun 123456                    # Rerun workflow
gh run download 123456                 # Download run artifacts
```

## Search

```bash
gh search repos "machine learning"     # Search repositories
gh search issues "bug label:urgent"    # Search issues
gh search prs "author:@me is:open"     # Search pull requests
gh search code "function" --language=python
```

## Gists

```bash
gh gist create file.txt                # Create gist from file
gh gist create --desc "Description"    # Create with description
gh gist list                           # List your gists
gh gist view abc123                    # View gist
gh gist edit abc123                    # Edit gist
gh gist clone abc123                   # Clone gist
gh gist delete abc123                  # Delete gist
```

## Codespaces

```bash
gh codespace create                    # Create codespace
gh codespace list                      # List codespaces
gh codespace ssh                       # SSH into codespace
gh codespace code                      # Open in VS Code
gh codespace ports                     # Manage port forwarding
gh codespace stop                      # Stop codespace
gh codespace delete                    # Delete codespace
```

## Projects (Beta)

```bash
gh project list                        # List projects
gh project create --title "Project"   # Create project
gh project view 123                    # View project
gh project item-add 123 --url "issue-url"  # Add item to project
gh project field-list 123             # List project fields
```

## Configuration & Extensions

### Configuration
```bash
gh config get editor                   # Get config value
gh config set editor vim               # Set config value
gh config list                         # List all config
```

### Extensions
```bash
gh extension list                      # List installed extensions
gh extension install owner/gh-ext      # Install extension
gh extension upgrade --all             # Update all extensions
gh extension remove owner/gh-ext       # Remove extension
```

## Global Options

```bash
--help                                 # Show help
--version                             # Show version
--repo owner/repo                     # Specify repository
--hostname github.enterprise.com      # Use GitHub Enterprise
--json                                # Output as JSON
```

## Pro Tips

- Use `gh alias` to create custom shortcuts
- Combine with `jq` for JSON processing: `gh pr list --json title,number | jq`
- Use `--web` flag to open items in browser
- Set default editor: `gh config set editor vim`
- Use tab completion in your shell for command completion