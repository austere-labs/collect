# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
uv sync
```

**Testing:**
```bash
pytest -v -s
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
python collect.py
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

### Key Features
- **Async token counting**: All providers support async token counting with proper chunking
- **Multi-model workflows**: Send content to all AI models concurrently via `multi_model_code_review()`
- **Content processing**: HTML-to-markdown conversion using readabilipy and markdownify
- **Automatic chunking**: Handles large content (>25k tokens) with intelligent splitting

### Configuration
Environment variables are loaded from `.env` file:
- GCP_PROJECT_ID (required)
- API key paths for Google Cloud Secret Manager
- Default model names for each provider
- Code review model configurations

### Testing Strategy
Each model has dedicated test files in `models/test_*.py`. Tests cover API integrations, token counting, and async functionality. Main functionality is tested in `test_collect.py` and `test_llmrunner.py`.

## Rules
- Never use python to run anything, always use uv run