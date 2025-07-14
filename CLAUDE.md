# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
uv sync
```

**Testing:**

### When running all tests, use the Makefile and run test-fast:
### here is an example

```bash
make test-fast
```
### OR use the following bash command:
```bash
uv run pytest -v -n auto -m "not slow"
```


## IMPORTANT: Always Always use uv run when running tests
### Here is an example
```bash
uv run pytest test_collect.py::test_function_name -v -s
# Run specific test: pytest test_collect.py::test_function_name -v -s
```
**Code Quality:**
```bash
make lint     # Run ruff check
make format   # Run black formatter
make check    # Run all: lint, format, test
```

**Run MCP Server:**
```bash
uv run collect.py
```

**Plan Management:**
```bash
# Sync plans from filesystem to database
uv run -m repository.plan_service

# Test plan service functionality
uv run pytest repository/test_plan_service.py -v -s

# Test plan database operations
uv run pytest repository/test_plan_service.py::test_sync_plans -v -s
```

## Planning System

This project uses a structured planning approach for feature development with plans organized in `_docs/plans/`. Plans progress through three stages:

### Plan Lifecycle
1. **`drafts/`** - Initial plans under development or consideration
2. **`approved/`** - Reviewed plans ready for implementation
3. **`completed/`** - Implemented plans with results documented

### Plan Document Format

#### Draft/Approved Plans Should Include:
```markdown
# Plan: [Clear Action-Oriented Title]

## Overview
Brief description of what needs to be implemented and why

## Implementation Steps
### 1. [Step Name]
Detailed implementation instructions including:
- Specific file locations and line numbers
- Function signatures with type hints
- Implementation pseudo-code or actual code
- Error handling approach

### 2. [Next Step]
...

## Key Features
- List of main features/capabilities
- Expected benefits

## Testing Considerations
- Test scenarios to implement
- Edge cases to handle
- Performance considerations

## Example Usage
```python
# Code examples demonstrating the feature
```
```

#### Completed Plans Add:
- **Status**: COMPLETED (YYYY-MM-DD)
- **Implementation Summary**: What was actually done
- **Results**: Outcomes, verification, test results
- **Files Modified**: List with ✅/❌ status indicators

### Plan Naming Conventions
- Use descriptive names with underscores: `add_improve_prompt.md`
- Start with action verbs: add, fix, implement, create, update
- Keep names concise but clear about the purpose

### Automated Plan Processing

The repository includes tools for automated plan implementation:

```python
# Build git worktrees for all approved plans
from mcp__collect__build_worktrees import build_worktrees
result = await build_worktrees(auto_process=True)  # Uses Claude Code SDK

# Sync plans between filesystem and database
from repository.plan_service import PlanService
service = PlanService(conn)
result = service.sync_plans()  # Loads plans into SQLite with JSONB
```

Branch names are automatically derived from plan filenames:
- `add_improve_prompt.md` → `feature/add-improve-prompt`
- Underscores become hyphens, `feature/` prefix added

### Plan Management Database

Plans are tracked in `data/plans.db` with:
- **plans** table: Current state with JSONB data field
- **plan_history**: Audit trail of changes
- **plan_metrics**: Analytics and performance data

Use the PlanService class to:
- Load plans from disk to database
- Track plan status changes
- Detect content changes via SHA256 hashing
- Query plans by status, tags, or content

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides web content fetching and multi-model AI analysis tools. The architecture follows these key patterns:

### Core Structure
- **collect.py**: Main MCP server entry point with FastMCP tool definitions
- **fetcher.py**: Handles URL fetching and content processing with clipboard integration
- **config.py**: Environment-based configuration with dotenv support
- **secret_manager.py**: Google Cloud Secret Manager integration for API keys

### Models Package
The `models/` directory contains unified API wrappers for different AI providers:
- **anthropic_mpc.py**: Anthropic Claude API integration
- **openai_mpc.py**: OpenAI API integration  
- **gemini_mcp.py**: Google Gemini API integration
- **xai_mcp.py**: XAI/Grok API integration

Each model wrapper follows the same pattern: configuration injection, secret management, and standardized methods like `send_message()`, `count_tokens()`, and `get_model_list()`.

### Packages
Additional specialized packages provide focused functionality:
- **reviewer/**: Code review automation system
  - `code_review.py`: CodeReviewer class for analyzing code diffs
  - Supports both file-based and git diff reviews
  - Generates individual model reviews and consolidated summaries
- **repository/**: Plan management and database operations
  - `plan_service.py`: PlanService class for filesystem-to-database sync
  - `plan_models.py`: Pydantic models for plan data with JSONB support
  - `database.py`: SQLite connection management with custom datetime adapters
  - Supports plan lifecycle tracking and content change detection


### Key Features
- **Async token counting**: All providers support async token counting with proper chunking
- **Multi-model workflows**: Send content to all AI models concurrently via `multi_model_code_review()`
- **Content processing**: HTML-to-markdown conversion using readabilipy and markdownify
- **Automatic chunking**: Handles large content (>25k tokens) with intelligent splitting
- **Code review system**: Automated code review via `run_code_review()` and `run_git_diff_review()` tools
- **Prompt engineering**: Generate optimized AI prompts using Anthropic's experimental API via `generate_prompt()`
- **Documentation extraction**: Intelligent section extraction from web docs using `get_docs()` with AI filtering
- **Clipboard integration**: Direct content copying with `copy_clipboard()` and automatic clipboard support in fetchers
- **Enhanced model features**: Gemini model listing with token limits, unified `extract_text()` methods across all providers

### Configuration
Environment variables are loaded from `.env` file:
- GCP_PROJECT_ID (required)
- API key paths for Google Cloud Secret Manager:
  - ANTHROPIC_API_KEY_PATH
  - OPENAI_API_KEY_PATH
  - GEMINI_API_KEY_PATH
  - XAI_API_KEY_PATH
- Default model names for each provider
- Code review model configurations

### Directory Structure
```
collect/
├── data/
│   ├── prompts.db      # Original prompts database
│   └── plans.db        # Plan management database
├── _docs/
│   └── plans/
│       ├── drafts/     # Plans under development
│       ├── approved/   # Plans ready for implementation
│       └── completed/  # Implemented plans with results
├── migrations/         # Database migrations for prompts.db
├── migrations-plans/   # Database migrations for plans.db
├── repository/         # Plan management system
│   ├── plan_service.py # Plan filesystem-to-database sync
│   ├── plan_models.py  # Pydantic models for plan data
│   └── database.py     # SQLite connection management
├── models/            # AI provider API wrappers
└── reviewer/          # Code review automation
```

### Testing Strategy
- **IMPORTANT**:  When writing and designing tests, we only want live direct integration tests. Please only create live direct integration testing. Please do not use mocks. 

## Rules
- **IMPORTANT**: YOU MUST always use `uv run` to run tests.

## Workflow Rules
- I do not want a pr created if I don't have a branch already
