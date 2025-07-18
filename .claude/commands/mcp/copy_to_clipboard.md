# Copy to Clipboard Tool

This command helps you copy various types of content to the system clipboard using the MCP `copy_clipboard` tool.

## Tool Definition

```python
@mcp.tool()
async def copy_clipboard(text: str):
    """Copy text to the system clipboard"""
    pyperclip.copy(text)
```

## Usage Instructions

Use the `mcp__collect__copy_clipboard` tool to copy content based on the user's request from `$ARGUMENTS`.

### Common Use Cases

1. **Code Snippets**: Copy formatted code blocks
2. **Configuration**: Copy config files, environment variables, or settings
3. **Documentation**: Copy markdown, text, or formatted content
4. **Data**: Copy JSON, CSV, or other structured data
5. **URLs/Links**: Copy lists of URLs or reference links
6. **Command Output**: Copy results from previous operations

### Best Practices

- **Format appropriately**: Ensure text is properly formatted for the intended use
- **Include context**: Add comments or headers when helpful
- **Validate content**: Check that sensitive information is not included
- **Optimize for paste destination**: Consider where the user will paste the content

### Example Workflows

**Copy code with context:**
```
# Configuration for Production Environment
DATABASE_URL=postgresql://user:pass@host:5432/db
API_KEY=your-api-key-here
DEBUG=false
```

**Copy structured data:**
```json
{
  "urls": [
    "https://example.com/api/endpoint1",
    "https://example.com/api/endpoint2"
  ],
  "headers": {
    "Authorization": "Bearer token",
    "Content-Type": "application/json"
  }
}
```

## Task: Copy Content to Clipboard

Based on the user's request in `$ARGUMENTS`, use the `mcp__collect__copy_clipboard` tool to copy the appropriate content to their system clipboard. Ensure the content is well-formatted and ready for their intended use.

