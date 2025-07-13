# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
uv sync
```

**Testing:**
## IMPORTANT: Always Always use uv run when running tests
### Here is an example
```bash
uv run pytest test_collect.py::test_function_name -v -s
# Run specific test: pytest test_collect.py::test_function_name -v -s
```
### When running all tests, use the Makefile and run test-fast:
### here is an example
```bash
make test-fast
```
### OR use the following bash command:
```bash
uv run pytest -v -n auto -m "not slow"
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
- **polygon/**: Financial market data integration
  - `client.py`: Async Polygon.io API client with automatic rate limiting
  - `models.py`: Pydantic models for OHLCV bars and API responses
  - Supports cryptocurrency and stock market data fetching
- **reviewer/**: Code review automation system
  - `code_review.py`: CodeReviewer class for analyzing code diffs
  - Supports both file-based and git diff reviews
  - Generates individual model reviews and consolidated summaries


### Key Features
- **Async token counting**: All providers support async token counting with proper chunking
- **Multi-model workflows**: Send content to all AI models concurrently via `multi_model_code_review()`
- **Content processing**: HTML-to-markdown conversion using readabilipy and markdownify
- **Automatic chunking**: Handles large content (>25k tokens) with intelligent splitting
- **Code review system**: Automated code review via `run_code_review()` and `run_git_diff_review()` tools
- **Prompt engineering**: Generate optimized AI prompts using Anthropic's experimental API via `generate_prompt()`
- **Financial data integration**: Fetch stock/crypto OHLCV data from Polygon.io via `use_polygon()`
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
  - POLYGON_API_KEY_PATH
- Default model names for each provider
- Code review model configurations

### Testing Strategy
- **IMPORTANT**:  When writing and designing tests, we only want live direct integration tests. Please only create live direct integration testing. Please do not use mocks. 

## Rules
- **IMPORTANT**: YOU MUST always use `uv run` to run tests.

## Workflow Rules
- I do not want a pr created if I don't have a branch already
