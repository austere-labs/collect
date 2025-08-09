# Convert Command File to Gemini CLI TOML Format

Please convert the file at {{file}} to TOML format following the Gemini CLI custom commands specification and copy the result to my clipboard.

## Gemini CLI Custom Commands Documentation

### TOML File Format Requirements

#### Required Fields
- `prompt` (String): The prompt that will be sent to the Gemini model when the command is executed. Use multi-line strings with triple quotes for multi-line prompts.

#### Optional Fields  
- `description` (String): A brief, one-line description of what the command does. This appears in the `/help` menu.

### Argument Handling Methods

1. **Shorthand Injection with `{{args}}`**
   - If the original file contains placeholders like `$ARGUMENTS`, `{file_name}`, or similar, replace them with `{{args}}`
   - The CLI will replace `{{args}}` with all text the user types after the command name
   - Example: `prompt = "Fix this issue: {{args}}."`

2. **Default Argument Handling**
   - If no `{{args}}` placeholder is used, arguments are automatically appended to the prompt after two newlines
   - Good for commands that need both instructions and user input

### Conversion Instructions

1. **Read the file at {{file}}**
2. **Extract the core prompt/instructions** from the markdown or text content
3. **Create a TOML structure with:**
   - A descriptive `description` field (one line, explains the command's purpose)
   - A `prompt` field containing the instructions
4. **Replace any argument placeholders** (like `$ARGUMENTS`, `{file_name}`, etc.) with `{{args}}`
5. **Use triple quotes** (`"""`) for multi-line prompts to preserve formatting
6. **Preserve any important formatting** like markdown, code blocks, or lists

### Example Conversions

**From Markdown:**
```markdown
Read the file at path: {file_name}

IMPORTANT:
- Only read the file
- Don't make changes
```

**To TOML:**
```toml
description = "Read a file and display its contents"
prompt = """Read the file at path: {{args}}

IMPORTANT:
- Only read the file
- Don't make changes"""
```

### Output Requirements

1. Copy the complete TOML content to the clipboard
2. The TOML should be ready to save as a `.toml` file
3. Ensure proper escaping of special characters if needed
4. Maintain the original intent and functionality of the command

Please proceed with converting {{file}} to TOML format and copying the result to my clipboard.