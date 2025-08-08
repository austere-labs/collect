# Extract Documentation from URLs

Use the `get_docs` MCP tool to extract specific documentation sections from web pages using Gemini 2.5 Flash.

## Usage

```
Use the get_docs tool with:
- url: $ARGUMENTS[0] (The URL of the documentation page)
- extract_value: $ARGUMENTS[1] (The specific section/function/topic to extract)

Example: get_docs($ARGUMENTS[0], $ARGUMENTS[1])
```

## What it does

This tool:
1. Fetches content from the specified URL
2. Uses Gemini 2.5 Flash Preview to intelligently extract documentation for the requested section
3. Returns the relevant documentation as clean, readable text

## Best for

- API documentation extraction
- Function/method documentation
- Specific topic documentation from larger pages
- Technical documentation that needs focused extraction

## Examples

Extract Python json.dumps documentation:
```
get_docs("https://docs.python.org/3/library/json.html", "json.dumps")
```

Extract React useEffect documentation:
```
get_docs("https://react.dev/reference/react/useEffect", "useEffect")
```

Extract specific AWS service documentation:
```
get_docs("https://docs.aws.amazon.com/s3/latest/userguide/", "bucket policies")
```

## Command Template

When called, this will execute:
```
get_docs($ARGUMENTS[0], $ARGUMENTS[1])
```
