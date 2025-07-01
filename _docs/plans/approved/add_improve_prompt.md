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
    messages: str,
    system: str = "",
    feedback: str,
    target_model: str = None
) -> str:
```

**Parameters:**
- `messages`: The prompt text to improve (as a simple string)
- `system`: System prompt (optional, defaults to empty string)
- `feedback`: Improvement instructions (required) - describes how to improve the prompt
- `target_model`: Target model for optimization (optional)

**Returns:** 
- Formatted string containing the improved prompt

### 2. Tool Structure

```python
# Pseudo-code structure
def improve_prompt(...):
    # 1. Validate input parameters
    #    - Ensure messages is not empty
    #    - Validate feedback is not empty
    
    # 2. Convert string message to API format
    formatted_messages = [{
        "role": "user",
        "content": [{"type": "text", "text": messages.strip()}]
    }]
    
    # 3. Create AnthropicMCP client instance
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    anthropic_mcp = AnthropicMCP(config, secret_mgr, config.anthropic_model_sonnet)
    
    # 4. Format data dict matching API requirements
    data = {
        "messages": formatted_messages,
        "system": system,
        "feedback": feedback.strip(),
    }
    if target_model:
        data["target_model"] = target_model
    
    # 5. Call anthropic_mcp.improve_prompt(data)
    response = anthropic_mcp.improve_prompt(data)
    
    # 6. Extract and return improved prompt as string
```

### 3. Error Handling

- **Input Validation:**
  - Check messages is not empty string
  - Ensure feedback is provided and not empty
  - Validate messages is a string type

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
    messages: The prompt text to improve as a simple string.
              Example: "Tell me about Python"
    system: Optional system prompt to improve (default: "")
    feedback: Instructions on how to improve the prompt.
              Examples:
              - "Make this more specific for beginners"
              - "Add more technical detail"
              - "Focus on security best practices"
    target_model: Optional model to optimize for (e.g., "claude-3-opus")

Returns:
    A formatted string containing the improved prompt

Example:
    >>> result = await improve_prompt(
    ...     messages="Tell me about Python",
    ...     system="You are a helpful assistant",
    ...     feedback="Make this more specific for a beginner learning web development"
    ... )
    >>> print(result)
    "I'm a beginner learning web development. Can you explain Python to me..."

Note:
    This uses Anthropic's experimental "prompt-tools" API which requires special
    access. The API is in closed research preview and may change without notice.
"""
```

## Key Features

1. **Simple string input** - Just pass your prompt as a plain string
2. **Flexible improvement via feedback** - User specifies exactly how to improve the prompt
3. **Returns improved prompt as string** - Easy to use result
4. **Model-specific optimization** - Can target improvements for specific Claude models
5. **Automatic formatting** - Handles API message structure internally

## Testing Considerations

- Test with various prompt strings (short, long, multiline)
- Verify feedback parameter validation
- Test error handling for empty strings
- Ensure proper formatting of output string
- Test with and without system prompts
- Verify target_model parameter functionality

## Example Usage in Practice

```python
# Improving a code review prompt
improved = await improve_prompt(
    messages="Review this Python code",
    system="You are a code reviewer",
    feedback="Make this more specific for security-focused code review with clear checklist items"
)

# Improving a tutorial prompt
improved = await improve_prompt(
    messages="Explain how to use async/await in JavaScript",
    feedback="Make this more beginner-friendly with practical examples"
)

# Improving a data analysis prompt
improved = await improve_prompt(
    messages="Analyze this dataset and find patterns",
    system="You are a data scientist",
    feedback="Add specific statistical methods and visualization requirements",
    target_model="claude-3-opus"
)
```
