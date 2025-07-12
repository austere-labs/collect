# Build Context - Code Extraction Only

**⚠️ CRITICAL INSTRUCTION: DO NOT TAKE ANY ACTIONS BEYOND CONTEXT BUILDING ⚠️**

You are ONLY extracting code for analysis. Do not:
- Make any changes to files
- Run tests or builds  
- Create new files
- Suggest improvements
- Execute any commands except the extract tool

Your sole purpose is to gather relevant code using the @tools/extract script.

## Usage

Call this template with arguments:
```
@build_context {{file_path}} {{function_signature}}
```

## Current Task

Extract the following function:
- **File/Directory**: `{{file_path}}`
- **Function Signature**: `{{function_signature}}`

Execute this command:
```bash
@tools/extract "{{file_path}}" "{{function_signature}}"
```

## Parameters

- **file_or_directory**: Path to search (single file or directory)
- **function_signature**: Exact function signature to find (must be quoted)

## Language Support

- **Python**: Indentation-based extraction
- **JavaScript**: Brace-based extraction  
- **Go**: Brace-based extraction

## Example Usage

**Python Function:**
```
@build_context . "async def fetch_urls(urls: List[str], ctx: Context = None) -> str:"
```

**JavaScript Function:**
```
@build_context app.js "function processData(items) {"
```

**Go Function:**
```
@build_context main.go "func handleRequest(w http.ResponseWriter, r *http.Request) {"
```

**Class Method:**
```
@build_context models/ "def send_message(self, prompt: str) -> str:"
```

## Instructions

1. Execute the extract command shown above
2. Present the extracted code without commentary
3. Stop - do not analyze or suggest changes

## Notes

- Function signatures are case-sensitive and whitespace-sensitive
- Leading whitespace is automatically trimmed
- Can extract from single files or entire directories
- Use quotes around function signatures to handle special characters
