# Extract Function

Extract a complete function or method from source code using the `extract` command.

## Usage

```bash
extract {{fileName}} {{functionSignature}}
```

## Arguments

- `fileName` - Path to the file or directory containing the function (e.g., `repository/plan_service.py` or `.` for current directory)
- `functionSignature` - The exact function signature to search for (must be quoted)

## Examples with expanded variables of {{fileName}} {{functionSignature}}

**Python:**
```bash
# Search in a specific file
extract repository/plan_service.py "def load_files(self):"
extract fetcher.py "async def fetch_urls(self, urls: List[str]) -> str:"

# Search in current directory
extract . "def sync_plans(self) -> Dict[str, Any]:"
```

**JavaScript:**
```bash
extract app.js "async function processData(items) {"
extract src/ "function handleClick(event) {"
```

**Go:**
```bash
extract main.go "func handleRequest(w http.ResponseWriter, r *http.Request) {"
extract . "func NewServer() *Server {"
```

## Description

This command uses ripgrep to locate and extract complete function or method definitions from source files. The `extract` command is available in your PATH and supports:

- **Python**: Indentation-based extraction (handles nested functions, decorators, and docstrings)
- **JavaScript**: Brace-based extraction (handles arrow functions and closures)
- **Go**: Brace-based extraction (handles methods and interfaces)

## Output

The extracted function is displayed with:
- File location and line number (e.g., `repository/plan_service.py:45`)
- Detected language (Python, JavaScript, or Go)
- Complete function code with original formatting preserved
- Colorized output for better readability

## Important Notes

- **Exact Match Required**: Function signatures must match exactly (case-sensitive and whitespace-sensitive)
- **Leading Whitespace**: Any leading whitespace in the signature is automatically trimmed
- **Search Scope**: Can search a single file or recursively search directories
- **Supported Extensions**: `.py` (Python), `.js` (JavaScript), `.go` (Go)

## Troubleshooting

- If function is not found, verify the exact signature by checking the source file
- For methods, include `self` or class parameters in the signature
- For decorated functions, use the function definition line, not the decorator

## IMPORTANT

This is a **read-only** operation that extracts and displays function code. After the extraction completes, **wait for further instructions** before taking any actions or making decisions based on the extracted code.
