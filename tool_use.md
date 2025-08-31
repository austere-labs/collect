# Tool Use Example

Here's an example usage for creating a Tool for the `convert_markdown_to_toml_gemini` function:

```python
from models.anthropic_models import Tool, ToolInputSchema, AnthropicRequest, Message, ToolChoice

# Define the tool
markdown_to_toml_tool = Tool(
    name="convert_markdown_to_toml",
    description="Convert markdown document to TOML format using Gemini CLI. Extracts key information and structures it as valid TOML.",
    input_schema=ToolInputSchema(
        properties={
            "markdown_doc": {
                "type": "string",
                "description": "The markdown document content to convert to TOML format"
            },
            "model": {
                "type": "string", 
                "description": "The Gemini model to use for conversion",
                "default": "gemini-2.0-flash-exp"
            }
        },
        required=["markdown_doc"]
    )
)

# Use in AnthropicRequest
request = AnthropicRequest(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        Message(role="user", content="Convert this README to TOML: # My Project\nThis is a sample project...")
    ],
    tools=[markdown_to_toml_tool],
    tool_choice=ToolChoice(type="auto")
)
```

## Tool Use Response

When Claude uses this tool, it might generate:
```json
{
    "type": "tool_use",
    "id": "toolu_123",
    "name": "convert_markdown_to_toml",
    "input": {
        "markdown_doc": "# My Project\nThis is a sample project...",
        "model": "gemini-2.0-flash-exp"
    }
}
```

You'd then call your function with the tool input and return the result.

## Function Implementation

```python
def convert_markdown_to_toml_gemini(
        markdown_doc: str,
        model: str = GEMINI_MODEL
) -> str:
    """
    Convert markdown to TOML using Gemini CLI.
    """

    prompt = """Convert the following markdown document to a TOML format.
      Extract all key information and structure it as valid TOML.
      Return ONLY the TOML content, no explanations or markdown formatting.

      Markdown content:
      {content}
      """

    prompt_with_args = prompt.format(content=markdown_doc)

    try:
        result = subprocess.run(
            ["gemini", "--model", model, "--prompt", "-"],
            input=prompt_with_args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error calling gemini: {e}")
        return f"#Error converting markdown\n# {str(e)}"
```