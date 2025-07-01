# MCP Server for local personal development

## A set of tools, writen in python that provides allows for fast and efficient context engineering and is designed to work with any existing tools that support MCP. The focus is mostly on utilizing the Claude ecosystem and prompting approaches using /slash commands and prompt engineering to orchestrate clean and optimal context into a LLM. 

## The MCP tools available in this project are:

**Web Content & Processing:**
- `fetch_url` - Fetch raw content from a single URL
- `fetch_urls` - Fetch content from multiple URLs concurrently
- `get_docs` - Extract specific documentation sections from web pages
- `to_markdown` - Convert HTML to markdown format
- `strip_html` - Remove HTML tags to get plain text
- `copy_clipboard` - Copy text to system clipboard

**AI Model Information:**
- `get_anthropic_model_list` - List available Claude models
- `get_openai_model_list` - List available GPT models
- `get_xai_model_list` - List available Grok models
- `get_gemini_model_list` - List Gemini models with token limits

**Token Counting:**
- `count_openai_tokens` - Count tokens for OpenAI models
- `count_anthropic_tokens` - Count tokens for Claude models
- `count_gemini_tokens` - Count tokens for Gemini models
- `count_grok_tokens` - Count tokens for Grok models

**Code Review:**
- `run_code_review` - Review code from a diff file using multiple LLMs
- `run_git_diff_review` - Review git diff changes

**Prompt Improvement:**  
- `generate_prompt` - Generate optimized AI prompts using Anthropic's experimental API

**Other Tools:**
- `use_polygon` - Fetch financial market data from Polygon.io


