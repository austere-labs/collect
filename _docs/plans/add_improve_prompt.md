# Plan: Add Improve Prompt MCP Tool

## Overview
Create a new MCP tool in `collect.py` that leverages Anthropic's experimental prompt improvement API to enhance existing prompts based on user feedback.

## Implementation Steps

### 1. Add the improve_prompt MCP tool
Location: After line 574 in collect.py

**Function Signature:**
```python
@mcp.tool()
async def improve_prompt(
    messages: List[dict],
    system: str = "",
    feedback: str,
    target_model: str = None
) -> str:
```

**Parameters:**
- `messages`: List of message dictionaries with role and content
  - Each message must have `role` ("user" or "assistant") and `content` fields
  - Content is a list of dicts with `type` and `text` fields
- `system`: System prompt (optional, defaults to empty string)
- `feedback`: Improvement instructions (required) - describes how to improve the prompt
- `target_model`: Target model for optimization (optional)

**Returns:** 
- Formatted string containing the improved messages (user prompt and assistant prefill)

### 2. Tool Structure

```python
# Pseudo-code structure
def improve_prompt(...):
    # 1. Validate input parameters
    #    - Ensure messages is a list with at least one user message
    #    - Validate feedback is not empty
    
    # 2. Create AnthropicMCP client instance
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    anthropic_mcp = AnthropicMCP(config, secret_mgr, config.anthropic_model_sonnet)
    
    # 3. Format data dict matching API requirements
    data = {
        "messages": messages,
        "system": system,
        "feedback": feedback.strip(),
    }
    if target_model:
        data["target_model"] = target_model
    
    # 4. Call anthropic_mcp.improve_prompt(data)
    response = anthropic_mcp.improve_prompt(data)
    
    # 5. Extract and return improved messages
    # Format both user and assistant messages into readable output
```

### 3. Error Handling

- **Input Validation:**
  - Check messages structure and content
  - Ensure feedback is provided and not empty
  - Validate message format (role, content structure)

- **API Errors:**
  - Catch `RuntimeError` from API failures
  - Catch `ValueError` for missing configuration
  - Provide meaningful error messages

### 4. Documentation

**Docstring Template:**
```python
"""
Improve an existing prompt using Anthropic's experimental prompt improvement API.

This tool analyzes an existing conversation prompt and enhances it based on 
provided feedback. It's useful for making prompts more specific, clear, or 
optimized for particular use cases.

Use this tool when you need to:
- Make prompts more specific or detailed
- Adapt prompts for different skill levels
- Optimize prompts for particular models
- Clarify ambiguous instructions
- Add missing context or constraints

Args:
    messages: List of message dictionaries representing the conversation.
              Each message must have 'role' and 'content' fields.
              Example: [{"role": "user", "content": [{"type": "text", "text": "..."}]}]
    system: Optional system prompt to improve (default: "")
    feedback: Instructions on how to improve the prompt.
              Examples:
              - "Make this more specific for beginners"
              - "Add more technical detail"
              - "Focus on security best practices"
    target_model: Optional model to optimize for (e.g., "claude-3-opus")

Returns:
    A formatted string containing:
    - The improved user prompt
    - The assistant prefill (if provided)
    - Usage statistics

Example:
    >>> messages = [{"role": "user", "content": [{"type": "text", "text": "Tell me about Python"}]}]
    >>> result = await improve_prompt(
    ...     messages=messages,
    ...     system="You are a helpful assistant",
    ...     feedback="Make this more specific for a beginner learning web development"
    ... )
    >>> print(result)
    "Improved prompt: I'm a beginner learning web development..."

Note:
    This uses Anthropic's experimental "prompt-tools" API which requires special
    access. The API is in closed research preview and may change without notice.
"""
```

## Key Features

1. **Accepts existing conversation context** - Can improve prompts with full conversation history
2. **Flexible improvement via feedback** - User specifies exactly how to improve the prompt
3. **Returns comprehensive output** - Includes both improved prompt and assistant prefill
4. **Model-specific optimization** - Can target improvements for specific Claude models
5. **Preserves conversation structure** - Maintains the role-based message format

## Testing Considerations

- Test with various message structures (single user message, multi-turn conversations)
- Verify feedback parameter validation
- Test error handling for malformed messages
- Ensure proper formatting of output string
- Test with and without system prompts
- Verify target_model parameter functionality

## Example Usage in Practice

```python
# Improving a code review prompt
messages = [{
    "role": "user", 
    "content": [{"type": "text", "text": "Review this Python code"}]
}]

improved = await improve_prompt(
    messages=messages,
    system="You are a code reviewer",
    feedback="Make this more specific for security-focused code review with clear checklist items"
)
```