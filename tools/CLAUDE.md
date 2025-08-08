# Tools Directory Documentation

This directory contains utility scripts for project management, development workflow, and automation. All tools support `--help` and `--llm` flags for detailed usage information.

## Available Tools

### 📦 Project Creation Tools

#### `newpy`
Creates a complete Python project with FastAPI, UV dependency management, and full development tooling.

**Usage:**
```bash
newpy <project_name>
```

**Features:**
- UV-based dependency management with virtual environment
- FastAPI web framework with uvicorn server
- Database setup with SQLite and yoyo-migrations
- Development tools: ruff, black, pytest
- Docker support with Dockerfile
- Makefile with common commands
- Environment configuration (.env, .env.local)
- Automatically downloads additional tools via fetchall
- Launches Claude Code after creation

**Example:**
```bash
newpy my-api-server
# Creates ~/python/my-api-server/ with full project structure
```

#### `startmcp`
Creates an MCP (Model Context Protocol) server project using FastMCP framework.

**Usage:**
```bash
startmcp <project_name>
```

**Features:**
- FastMCP server template
- MCP dependencies (mcp, pytest-asyncio)
- Testing setup with pytest
- Environment configuration
- Makefile with test commands (including parallel test execution)
- Launches Claude Code after creation

**Example:**
```bash
startmcp my-mcp-server
# Creates ~/python/my-mcp-server/ with MCP server structure
```

### 🗄️ Database Tools

#### `createdb`
Creates a new SQLite database in the data/ directory.

**Usage:**
```bash
createdb <database_name>
```

**Features:**
- Creates data/ directory if needed
- Adds .db extension automatically
- Sets appropriate file permissions (644)
- Validates sqlite3 availability

**Example:**
```bash
createdb myapp
# Creates data/myapp.db
```

### 🌳 Git Workflow Tools

#### `trees`
Creates two git worktrees for parallel feature development.

**Usage:**
```bash
trees
```

**Features:**
- Creates two worktrees in parent directory
- Names: `<project>-wt1` (branch: feature1) and `<project>-wt2` (branch: feature2)
- Automatic branch creation
- Color-coded output

**Example:**
```bash
cd ~/python/myproject
trees
# Creates ../myproject-wt1 and ../myproject-wt2
```

#### `killtrees`
Removes worktrees and branches created by the trees script.

**Usage:**
```bash
killtrees
```

**Features:**
- Removes both worktrees forcefully
- Deletes associated branches (feature1, feature2)
- Prunes worktree entries
- Safe error handling for missing worktrees

**Example:**
```bash
killtrees
# Removes worktrees and cleans up branches
```

### 🔍 Code Analysis Tools

#### `extract`
Extracts complete function definitions from source code files.

**Usage:**
```bash
extract <file_or_directory> "<function_signature>"
```

**Features:**
- Supports Python, JavaScript, and Go
- Uses ripgrep for fast searching
- Intelligent extraction:
  - Python: indentation-based
  - JavaScript/Go: brace-matching
- Preserves formatting and comments
- Shows file location and line numbers

**Examples:**
```bash
# Extract Python async function
extract . "async def fetch_urls(urls: List[str], ctx: Context = None) -> str:"

# Extract JavaScript function
extract app.js "function processData(items) {"

# Extract Go function
extract main.go "func handleRequest(w http.ResponseWriter, r *http.Request) {"
```

### 📥 Resource Management Tools

#### `fetchall`
Downloads resources from the austere-labs/collect GitHub repository.

**Usage:**
```bash
fetchall [options]
```

**Options:**
- `--force`: Overwrite existing files
- `--help`: Show usage information
- `--llm`: Show detailed LLM-formatted documentation

**Downloads:**
- `movetools`: Single script file (if available)
- `tools/*`: All scripts from tools directory
- `.claude/commands/*.md`: Command templates (recursive)
- `.gemini/commands/*.md`: Gemini templates (or copies from .claude)
- `guides/*.md`: Documentation guides

**Features:**
- Smart parent directory detection (works from tools/ subdirectory)
- Auto-creates necessary directories
- Sets executable permissions on scripts
- Progress indicators with color output
- Category-based summary statistics
- Skips existing files by default (use --force to overwrite)
- Automatic .claude → .gemini copying if needed

**Example:**
```bash
fetchall          # Download all, skip existing
fetchall --force  # Download all, overwrite existing
```

## Common Patterns

### Tool Flags
All tools support consistent flags:
- `--help` or `-h`: Display usage information
- `--llm`: Show detailed LLM-oriented documentation

### Directory Structure
Tools typically work with this structure:
```
~/python/
├── <project_name>/
│   ├── .venv/
│   ├── data/
│   ├── tools/
│   ├── .claude/commands/
│   ├── .gemini/commands/
│   ├── guides/
│   ├── migrations/
│   └── repository/
```

### Error Handling
- All scripts use `set -e` for fail-fast behavior
- Color-coded output (green=success, red=error, yellow=warning, blue=info)
- Validation of required commands (sqlite3, gh, rg, etc.)
- Safe handling of existing files and directories

## Requirements

### System Dependencies
- **bash**: All scripts are bash-based
- **uv**: Required for Python project creation (newpy, startmcp)
- **sqlite3**: Required for database creation
- **git**: Required for worktree management
- **gh**: GitHub CLI for fetchall
- **jq**: JSON processor for fetchall
- **ripgrep** (`rg`): Required for extract tool (expects at /opt/homebrew/bin/rg)

### Python Environment
- Python 3.11+ recommended for created projects
- Virtual environments managed by UV

## Integration with Claude Code

Several tools integrate with Claude Code:
- `newpy` and `startmcp` automatically launch Claude Code after project creation
- Projects include `.mcp.json` configuration for MCP server integration
- `.claude/commands/` directories for command templates

## Best Practices

1. **Project Creation**: Use `newpy` for FastAPI projects, `startmcp` for MCP servers
2. **Worktrees**: Use `trees` for parallel feature development, clean up with `killtrees`
3. **Resources**: Run `fetchall` in new projects to get latest tools and templates
4. **Databases**: Use `createdb` to maintain consistent database creation
5. **Code Search**: Use `extract` for precise function extraction with proper context

## Troubleshooting

### Common Issues

**fetchall fails to download:**
- Ensure GitHub CLI (`gh`) is installed and authenticated
- Check network connectivity
- Verify repository access permissions

**extract doesn't find functions:**
- Ensure function signature is quoted properly
- Check that ripgrep is installed at expected path
- Verify file extensions match supported languages

**Project creation fails:**
- Ensure UV is installed and in PATH
- Check write permissions in ~/python/
- Verify Python version compatibility

**Worktree creation fails:**
- Ensure you're in a git repository
- Check for uncommitted changes
- Verify no existing worktrees with same names