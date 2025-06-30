# Plan: Add Templatize Prompt MCP Tool

## Overview
Create a new MCP tool in `collect.py` that leverages Anthropic's experimental prompt templatization API to convert specific prompts into reusable templates with variable placeholders.

## Implementation Steps

### 1. Add the templatize_prompt MCP tool
Location: After the generate_prompt tool (around line 575 in collect.py)

**Function Signature:**
```python
@mcp.tool()
async def templatize_prompt(
    messages: str,
    system: str = "",
    instructions: str = "",
    target_model: str = None
) -> str:
```

**Parameters:**
- `messages`: A string containing the prompt text to templatize
  - Will be automatically formatted into the required message structure
  - Treated as a user message in the conversation
- `system`: System prompt to templatize (optional, defaults to empty string)
- `instructions`: Optional guidance for the templatization process
- `target_model`: Target model for optimization (optional)

**Returns:**
- Formatted string containing:
  - Templatized messages with variable placeholders
  - Templatized system prompt (if provided)
  - Extracted variable values
  - Usage statistics

### 2. Tool Structure

```python
# Implementation structure
def templatize_prompt(...):
    # 1. Validate input parameters
    #    - Ensure messages string is not empty
    #    - Strip whitespace from messages
    
    # 2. Convert string messages to required format
    formatted_messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": messages.strip()}]
        }
    ]
    
    # 3. Create AnthropicMCP client instance
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    anthropic_mcp = AnthropicMCP(config, secret_mgr, config.anthropic_model_sonnet)
    
    # 4. Format data dict matching API requirements
    data = {
        "messages": formatted_messages,
        "system": system,
    }
    if instructions:
        data["instructions"] = instructions.strip()
    if target_model:
        data["target_model"] = target_model
    
    # 5. Call anthropic_mcp.templatize_prompt(data)
    response = anthropic_mcp.templatize_prompt(data)
    
    # 6. Format and return templatized output
    # Include templates, extracted variables, and usage stats
```

### 3. Error Handling

- **Input Validation:**
  - Check messages string is not empty
  - Strip and validate the prompt text
  - Ensure proper string formatting

- **API Errors:**
  - Catch `RuntimeError` from API failures
  - Catch `ValueError` for missing configuration
  - Provide meaningful error messages

### 4. Documentation

**Docstring:**
```python
"""
Convert a specific prompt into a reusable template using Anthropic's experimental templatization API.

This tool analyzes an existing prompt and automatically identifies variable parts,
replacing them with template placeholders. It's useful for creating reusable
prompt templates from specific examples.

Use this tool when you need to:
- Create reusable templates from specific prompts
- Build prompt libraries from existing conversations
- Standardize similar prompts with variable content
- Generate templates for repetitive tasks
- Extract patterns from existing prompts

Args:
    messages: A string containing the prompt text to templatize.
              This will be automatically formatted as a user message.
              Example: "Translate hello to German"
    system: Optional system prompt to templatize (default: "")
    instructions: Optional guidance for how to templatize the prompt.
                  Examples:
                  - "Focus on making location and product variables"
                  - "Extract technical terms as variables"
                  - "Keep formatting instructions fixed"
    target_model: Optional model to optimize for (e.g., "claude-3-opus")

Returns:
    A formatted string containing:
    - The templatized messages with {{VARIABLE}} placeholders
    - The templatized system prompt (if provided)
    - Extracted variable values
    - Usage statistics

Example:
    >>> result = await templatize_prompt(
    ...     messages="Translate hello to German",
    ...     system="You are a professional English to German translator",
    ...     instructions="Make the word to translate and target language variables"
    ... )
    >>> print(result)
    "Template: Translate {{WORD_TO_TRANSLATE}} to {{TARGET_LANGUAGE}}
     Variables: WORD_TO_TRANSLATE='hello', TARGET_LANGUAGE='German'"

Note:
    This uses Anthropic's experimental "prompt-tools" API which requires special
    access. The API is in closed research preview and may change without notice.
"""
```

### 5. Output Formatting

The tool should format the response to clearly show:
1. **Templatized Messages**: Show each message with variable placeholders
2. **System Template**: If provided, show the templatized system prompt
3. **Variable Mappings**: Display extracted variables and their original values
4. **Usage Stats**: Include token counts for transparency

Example output format:
```
=== Templatized Prompt ===
User: Translate {{WORD_TO_TRANSLATE}} to {{TARGET_LANGUAGE}}
System: You are a professional English to {{TARGET_LANGUAGE}} translator

=== Extracted Variables ===
WORD_TO_TRANSLATE: "hello"
TARGET_LANGUAGE: "German"

=== Usage ===
Input tokens: 490
Output tokens: 661
```

## Key Features

1. **Automatic variable extraction** - Identifies repeatable parts and creates meaningful variable names
2. **Flexible instructions** - User can guide the templatization process
3. **Preserves conversation structure** - Maintains the role-based message format
4. **System prompt support** - Can templatize system prompts alongside messages
5. **Clear variable mappings** - Shows what values were extracted into variables

## Testing Considerations

- Test with various prompt strings (simple and complex)
- Verify with and without system prompts
- Test different instruction styles
- Ensure proper formatting of template variables
- Verify variable extraction accuracy
- Test error handling for empty strings
- Test that string is properly converted to message format

## Example Usage Scenarios

```python
# 1. Creating a translation template
template = await templatize_prompt(
    messages="Please translate 'Good morning' from English to Spanish",
    instructions="Make source text, source language, and target language variables"
)

# 2. Creating a code review template
template = await templatize_prompt(
    messages="Review this Python function for security issues: def login(username, password): ...",
    system="You are a security-focused code reviewer",
    instructions="Make the code snippet and programming language variables"
)

# 3. Creating a data analysis template
template = await templatize_prompt(
    messages="Analyze sales data for Q3 2024 and identify top 5 trends",
    instructions="Make time period and number of trends variables"
)
```

## Differences from improve_prompt

- **Purpose**: templatize_prompt creates reusable templates, while improve_prompt enhances existing prompts
- **Output**: Returns templates with variables vs. improved specific prompts
- **Use case**: Building prompt libraries vs. optimizing individual prompts
- **Parameters**: Uses `instructions` instead of `feedback` to guide the process
