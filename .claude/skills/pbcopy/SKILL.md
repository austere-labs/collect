---
allowed-tools: Bash(pbcopy:*), Bash(echo:*), Bash(cat:*)
description: Copy content to clipboard using pbcopy
model: claude-sonnet-4-5-20250929
---

# Copy to Clipboard with pbcopy

You will receive an instruction in `$INSTRUCTION` and content in `$ARGUMENTS` that needs to be copied to the clipboard.

## Task

Based on the instruction provided, process the content from `$ARGUMENTS` and copy it to the clipboard using the `pbcopy` command.

## Implementation

Use the following approach:
1. Parse the instruction to understand what formatting or processing is needed
2. Prepare the content according to the instruction
3. Use `echo` with `pbcopy` to copy the content to the clipboard

### Examples of usage patterns:

**Simple text copy:**
```bash
echo "Your content here" | pbcopy
```

**Multi-line content:**
```bash
echo -e "Line 1\nLine 2\nLine 3" | pbcopy
```

**JSON formatting:**
```bash
echo '{"key": "value", "array": [1, 2, 3]}' | pbcopy
```

**Code snippet with proper formatting:**
```bash
cat << 'EOF' | pbcopy
def example_function():
    """Example Python function"""
    return "Hello, World!"
EOF
```

## Instructions

1. Analyze the `$INSTRUCTION` to determine:
   - What type of content needs to be copied
   - Any specific formatting requirements
   - Whether any processing or transformation is needed

2. Take the content from `$ARGUMENTS` and:
   - Apply any necessary formatting
   - Ensure proper escaping for special characters
   - Preserve the intended structure (indentation, line breaks, etc.)

3. Execute the appropriate bash command to copy the processed content to the clipboard

4. Confirm the operation completed successfully

## Common scenarios to handle:

- **Code snippets**: Preserve indentation and formatting
- **Configuration files**: Maintain structure and comments
- **URLs/Links**: Copy as-is or format as a list
- **JSON/YAML**: Ensure valid syntax
- **Commands**: Include any necessary escaping
- **Documentation**: Preserve markdown formatting

Always ensure the content is properly formatted for the user's intended use case based on the instruction provided.
