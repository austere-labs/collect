# Collect

An MCP (Model Context Protocol) server for fetching web content, processing HTML, and enabling multi-model AI analysis workflows.

## Features

- **Web Content Fetching**: Download and process content from multiple URLs with automatic chunking
- **HTML Processing**: Convert HTML to clean markdown or plain text using readabilipy and markdownify
- **Multi-Model AI Integration**: Unified access to OpenAI, Anthropic, Gemini, and XAI APIs
- **Code Review Workflows**: Send content to all AI models concurrently for comparison
- **Token Management**: Count tokens across different providers with automatic chunking for large content
- **Secure Configuration**: Google Cloud Secret Manager integration for API key storage

## MCP Tools

### Content Processing
- `collect(urls: List[str])` - Fetch content from multiple URLs, convert to markdown, handle chunking if >25k tokens
- `strip_html(html: str)` - Convert HTML to plain text using BeautifulSoup
- `to_markdown(html: str)` - Convert HTML to clean markdown using readabilipy and markdownify

### Multi-Model Analysis
- `multi_model_code_review(output_dir: str, from_file: str = "diff.md")` - Send content to all AI models concurrently

### Model Management
- `get_anthropic_model_list()` - Get available Anthropic models
- `get_openai_model_list()` - Get available OpenAI models (handles reasoning models like o1/o3)
- `get_xai_model_list()` - Get available XAI/Grok models

### Token Utilities
- `count_openai_tokens(text: str, model: str = "gpt-4")` - Count tokens using tiktoken
- `count_anthropic_tokens(text: str)` - Count tokens via Anthropic API
- `count_gemini_tokens(text: str)` - Count tokens via Gemini API
- `count_grok_tokens(text: str)` - Count tokens via XAI API

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment variables** in `.env`:
   ```bash
   # Required
   GCP_PROJECT_ID=your-gcp-project-id
   
   # API Key paths (for Google Cloud Secret Manager)
   ANTHROPIC_API_KEY_PATH=projects/PROJECT/secrets/anthropic-api-key/versions/latest
   OPENAI_API_KEY_PATH=projects/PROJECT/secrets/openai-api-key/versions/latest
   GEMINI_API_KEY_PATH=projects/PROJECT/secrets/gemini-api-key/versions/latest
   XAI_API_KEY_PATH=projects/PROJECT/secrets/xai-api-key/versions/latest
   
   # Optional: Default model names
   DEFAULT_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   DEFAULT_OPENAI_MODEL=gpt-4
   DEFAULT_GEMINI_MODEL=gemini-1.5-pro
   DEFAULT_XAI_MODEL=grok-beta
   ```

3. **Run the MCP server:**
   ```bash
   python collect.py
   ```

## MCP Configuration

Add to your Claude Code config (`.mcp.json`):
```json
{
  "collect": {
    "command": "/Users/benjaminmetz/.local/bin/uv",
    "args": [
      "--directory",
      "/Users/benjaminmetz/python/collect",
      "run",
      "collect.py"
    ]
  }
}
```

## Usage Examples

The server provides MCP tools for Claude Code and other MCP clients:

- **Fetch web content**: Automatically converts HTML to markdown and copies to clipboard
- **Code reviews**: Send diff files to multiple AI models for comparative analysis
- **Token counting**: Check token usage before sending to AI APIs
- **Content chunking**: Automatically splits large content when exceeding token limits

## Dependencies

Core dependencies include:
- `mcp[cli]` - MCP framework
- `httpx` - HTTP client for web fetching
- `anthropic`, `openai` - AI model APIs
- `google-cloud-aiplatform` - Gemini integration and token counting
- `tiktoken` - OpenAI token counting
- `readabilipy`, `markdownify` - HTML to markdown conversion
- `beautifulsoup4` - HTML parsing

## Testing

Run tests with:
```bash
pytest
```

Tests cover all MCP tools, AI model integrations, and async token counting functionality.

urls for testing fetcher:  
```

url1 = "https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md"
url2 = "https://modelcontextprotocol.io/llms-full.txt"


```
