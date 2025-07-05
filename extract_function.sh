#!/bin/bash

# Function extraction tool using ripgrep
# Supports Python, JavaScript, and Go

set -euo pipefail

RG = "/opt/homebrew/bin/rg"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 <file_or_directory> <function_signature>"
    echo ""
    echo "Examples:"
    echo "  $0 file.py \"async def fetch_urls(urls: List[str], ctx: Context = None) -> str:\""
    echo "  $0 . \"function processData(items) {\""
    echo "  $0 main.go \"func handleRequest(w http.ResponseWriter, r *http.Request) {\""
    echo ""
    echo "Supported languages: Python (.py), JavaScript (.js), Go (.go)"
    exit 1
}

# Check for --llm flag
if [ $# -eq 1 ] && [ "$1" = "--llm" ]; then
    usage
fi

# Check arguments
if [ $# -ne 2 ]; then
    usage
fi

FILE_OR_DIR="$1"
FUNCTION_SIGNATURE="$2"

# Function to extract Python function (indentation-based)
extract_python_function() {
    local file="$1"
    local line_num="$2"
    local signature="$3"
    
    # Get the indentation level of the function definition
    local indent=$($RG -n --no-heading --fixed-strings "$signature" "$file" | head -1 | sed 's/^[0-9]*://' | sed 's/\(^[ \t]*\).*/\1/' | wc -c)
    indent=$((indent - 1))
    
    # Extract from the function line until we return to same or lower indentation
    # or reach end of file
    awk -v start="$line_num" -v base_indent="$indent" '
        NR == start { print; in_function=1; next }
        in_function {
            # Skip empty lines and comments
            if (/^[ \t]*$/ || /^[ \t]*#/) {
                print
                next
            }
            # Check indentation
            match($0, /^[ \t]*/)
            current_indent = RLENGTH
            if (current_indent <= base_indent && $0 !~ /^[ \t]*$/) {
                exit
            }
            print
        }
    ' "$file"
}

# Function to extract JavaScript/Go function (brace-based)
extract_brace_function() {
    local file="$1"
    local line_num="$2"
    local signature="$3"
    
    # Extract from the function line, counting braces
    awk -v start="$line_num" '
        NR >= start {
            print
            # Count braces
            for (i = 1; i <= length($0); i++) {
                char = substr($0, i, 1)
                if (char == "{") brace_count++
                else if (char == "}") brace_count--
            }
            # If we started (found at least one brace) and now balanced, exit
            if (NR > start && brace_count == 0 && found_brace) exit
            if (brace_count > 0) found_brace = 1
        }
    ' "$file"
}

# Function to determine file type
get_file_type() {
    local file="$1"
    case "${file##*.}" in
        py) echo "python" ;;
        js) echo "javascript" ;;
        go) echo "go" ;;
        *) echo "unknown" ;;
    esac
}

# Search for the function signature
echo -e "${BLUE}Searching for function: ${YELLOW}$FUNCTION_SIGNATURE${NC}"

# Use ripgrep to find the function
# For simpler and more reliable matching, use fixed string search with looser matching
if [ -f "$FILE_OR_DIR" ]; then
    # Single file mode - search for the signature (without leading spaces)
    TRIMMED_SIG=$(echo "$FUNCTION_SIGNATURE" | sed 's/^[[:space:]]*//')
    MATCHES=$($RG -n --fixed-strings "$TRIMMED_SIG" "$FILE_OR_DIR" || true)
else
    # Directory mode - search only in supported files
    TRIMMED_SIG=$(echo "$FUNCTION_SIGNATURE" | sed 's/^[[:space:]]*//')
    MATCHES=$($RG -n --fixed-strings "$TRIMMED_SIG" -g "*.py" -g "*.js" -g "*.go" "$FILE_OR_DIR" || true)
fi

if [ -z "$MATCHES" ]; then
    echo -e "${RED}Error: Function signature not found${NC}"
    exit 1
fi

# Process each match
echo "$MATCHES" | while IFS=: read -r first second rest; do
    # Determine if we're in single file or directory mode
    if [ -f "$FILE_OR_DIR" ]; then
        # Single file mode: first is line number, FILE_OR_DIR is the file
        file="$FILE_OR_DIR"
        line_num="$first"
    else
        # Directory mode: first is file, second is line number
        file="$first"
        line_num="$second"
    fi
    
    FILE_TYPE=$(get_file_type "$file")
    
    if [ "$FILE_TYPE" = "unknown" ]; then
        echo -e "${RED}Error: Unsupported file type for $file${NC}"
        continue
    fi
    
    echo -e "\n${GREEN}Found in: ${NC}$file:$line_num"
    echo -e "${GREEN}Language: ${NC}$FILE_TYPE"
    echo -e "${GREEN}Function:${NC}"
    echo "----------------------------------------"
    
    case "$FILE_TYPE" in
        python)
            extract_python_function "$file" "$line_num" "$TRIMMED_SIG"
            ;;
        javascript|go)
            extract_brace_function "$file" "$line_num" "$TRIMMED_SIG"
            ;;
    esac
    
    echo "----------------------------------------"
done
