# Extract Function

Extract a complete function or method from source code using the extract_function.sh tool.

## Usage

```bash
./extract_function.sh {{fileName}} {{functionSignature}}
```

## Arguments

- `fileName` - Path to the file containing the function
- `functionSignature` - The exact function signature to search for

## Examples with expanded variables of {{fileName}} {{functionSignature}}

**Python:**
```bash
./extract_function.sh fetcher.py "async def fetch_urls(self, urls: List[str]) -> str:"
```

**JavaScript:**
```bash
./extract_function.sh app.js "async function processData(items) {"
```

**Go:**
```bash
./extract_function.sh main.go "func handleRequest(w http.ResponseWriter, r *http.Request) {"
```

## Description

This command uses ripgrep to locate and extract complete function or method definitions from source files. It supports:

- **Python**: Indentation-based extraction
- **JavaScript**: Brace-based extraction  
- **Go**: Brace-based extraction

The tool automatically detects the language based on file extension and uses the appropriate extraction method to capture the entire function body.

## Output

The extracted function is displayed with:
- File location and line number
- Detected language
- Complete function code with proper formatting
- Colorized output for better readability

## Notes

- Function signatures must match exactly (case-sensitive)
- Leading whitespace in signatures is automatically handled
- Can search single files or entire directories
- Supports nested functions and complex code structures
