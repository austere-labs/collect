---
description: "Using Claude Code WebFetch tool, call the url and uses the provided instructions to extract the appropriate data from the response"
allowed-tools: WebFetch
argument-hint: [url] [instructions]
model: claude-opus-4-20250514
---

## IMPORTANT INSTRUCTIONS:
- Please do not use any MCP tools.
- Only use the WebFetch tool

# WebFetch and Extract

Fetch content using a URL and extract specific information based on provided instructions.

## Usage

This prompt takes two arguments:
1. **URL**: The web address to search/fetch content from
2. **Extraction Instructions**: Specific instructions for what information to extract from the content

## Prompt Template

Please use the Fetch tool to search for content from this URL: `{url}`

After retrieving the content, please extract the following information based on these instructions:

`{extraction_instructions}`

Focus on providing only the requested information in a clear and concise format. If the requested information is not found in the content, please indicate that explicitly.

## Example Usage

**URL**: https://docs.python.org/3/library/datetime.html
**Extraction Instructions**: Extract all available datetime format codes and their descriptions

**URL**: https://github.com/anthropics/claude-code
**Extraction Instructions**: Find and summarize the main features and installation instructions

## Parameters

- `{url}` - Replace with the target URL
- `{extraction_instructions}` - Replace with specific instructions for what to extract from the content
