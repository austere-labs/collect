# Plan: GitHub Commands Sync and Conversion Script

## Overview
Create a comprehensive solution that:
1. Uses GitHub CLI to fetch `.claude/commands` from the remote repository `austere-labs/collect`
2. Creates local `.claude/commands` and `.gemini/commands` directory structures
3. Converts markdown command files to TOML format using Gemini 2.5 Pro
4. Maintains directory structure fidelity between remote and local systems

## Implementation Steps

### 1. Create main script file: `sync_commands.py`
- Use GitHub CLI commands exclusively for all GitHub operations
- Create functions for directory management and file operations
- Implement async pattern for efficient operations
- Follow project patterns using existing Config and SecretManager classes

### 2. Implement GitHub CLI integration functions
- `fetch_directory_tree()`: Use `gh api repos/austere-labs/collect/contents/.claude/commands` to get directory structure
- `download_file_content()`: Use `gh api repos/austere-labs/collect/contents/{path}` to download individual files
- `list_subdirectories()`: Use GitHub CLI to recursively discover all subdirectories
- `create_local_directories()`: Mirror remote structure locally using discovered paths
- All GitHub operations exclusively through `gh` CLI commands, no direct API calls

### 3. Create local directory management
- Check for existing `.claude/commands` directory in current project
- Create missing directories mirroring remote structure exactly
- Create equivalent `.gemini/commands` directory structure
- Preserve all subdirectory relationships

### 4. Implement `convert(prompt: str) -> str` function
- Use existing GeminiMCP class from `models/gemini_mcp.py`
- Create specialized prompt for markdown-to-TOML conversion
- Use Gemini 2.5 Pro model for high-quality conversions
- Handle token limits and error cases gracefully
- Preserve semantic meaning while adapting format structure

### 5. Add main orchestration function
- Pull all commands from GitHub using GitHub CLI exclusively
- Write files to local `.claude/commands` maintaining structure
- Convert each markdown file and write to corresponding `.gemini/commands` location
- Add comprehensive progress tracking and error handling
- Support dry-run mode for testing

## Key Features
- Exclusive GitHub CLI integration for secure, authenticated access
- Recursive directory structure replication with full fidelity
- AI-powered format conversion using Gemini 2.5 Pro
- Comprehensive error handling and progress reporting
- Integration with existing project architecture (Config, SecretManager, GeminiMCP)
- Support for both `.claude/commands` and `.gemini/commands` workflows

## Testing Considerations
- Test with various markdown command formats and edge cases
- Verify directory creation logic handles nested structures correctly
- Test conversion quality with sample files of different complexities
- Handle GitHub CLI authentication and network failures gracefully
- Verify TOML output is valid and semantically equivalent to markdown input

## Example Usage
```python
# Basic usage
from sync_commands import sync_and_convert_commands
await sync_and_convert_commands()

# With options
await sync_and_convert_commands(
    source_repo="austere-labs/collect",
    dry_run=True,
    convert_only=False
)
```

## Implementation Details

### GitHub CLI Commands to Use
```bash
# List directory contents
gh api repos/austere-labs/collect/contents/.claude/commands

# Get file content
gh api repos/austere-labs/collect/contents/.claude/commands/{filename}

# Recursive directory listing
gh api repos/austere-labs/collect/git/trees/HEAD?recursive=1
```

### Directory Structure Example
```
.claude/commands/
├── subdirectory1/
│   ├── command1.md
│   └── command2.md
└── subdirectory2/
    └── command3.md

.gemini/commands/
├── subdirectory1/
│   ├── command1.toml
│   └── command2.toml
└── subdirectory2/
    └── command3.toml
```

### Conversion Prompt Template
```
Convert the following markdown command to TOML format while preserving all semantic meaning and functionality:

[MARKDOWN_CONTENT]

Output should be valid TOML with appropriate sections and key-value pairs that represent the same information structure as the original markdown.
```
