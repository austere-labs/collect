# Collect

An MCP (Model Context Protocol) server for fetching URLs, converting content, and working with multiple AI models.

## Features

- **URL Collection**: Fetch content from multiple URLs with automatic token chunking
- **Content Conversion**: Convert HTML to clean markdown or plain text
- **Multi-Model Support**: Compare responses across AI providers (OpenAI, Anthropic, Gemini, XAI)
- **Token Management**: Smart chunking for large content and token counting utilities

## Tools

### Content Fetching
- `collect(urls)` - Fetch and concatenate content from multiple URLs
- `strip_html(html)` - Convert HTML to plain text
- `to_markdown(html)` - Convert HTML to clean markdown

### Multi-Model Analysis
- `multi_llm(from_file, models, output_dir)` - Send content to multiple AI models concurrently
- Model list functions for each provider

### Token Utilities
- Token counting for OpenAI, Anthropic, Gemini, and XAI models

## Setup

1. Install dependencies: `uv sync`
2. Configure environment variables in `.env`:
   ```
   GCP_PROJECT_ID=your-project
   ANTHROPIC_API_KEY_PATH=/path/to/key
   GEMINI_API_KEY_PATH=/path/to/key
   XAI_API_KEY_PATH=/path/to/key
   OPENAI_API_KEY_PATH=/path/to/key
   ```
3. Run: `python collect.py`

## MCP Configuration

Add to your Claude Code config:
```json
"collect": {
    "command": "/Users/benjaminmetz/.local/bin/uv",
    "args": [
        "--directory",
        "/Users/benjaminmetz/python/collect",
        "run",
        "collect.py"
    ]
}
```

## Usage

The server provides MCP tools for Claude Code and other MCP clients to fetch web content and analyze it across multiple AI models.
