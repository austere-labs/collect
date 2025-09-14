from secret_manager import SecretManager
from config import Config
import os
import subprocess
import tomllib
from typing import Tuple
from models.anthropic_models import Tool, ToolInputSchema


def fetch_gemini_key() -> str:
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    gemini_api_key = secret_mgr.get_secret(config.gemini_api_key_path)
    return gemini_api_key


os.environ["GOOGLE_API_KEY"] = fetch_gemini_key()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-opus-4-20250514"

# Define `convert_markdown_to_toml_gemini` as a Tool
# with ToolInputSchema for the Anthropic API
tool_convert_markdown_to_toml_gemini = Tool(
    name="convert_markdown_to_toml_gemini",
    description="""
        Convert markdown document to TOML format using Gemini CLI.
        Extracts key information and structures it as valid TOML.""",
    input_schema=ToolInputSchema(
        properties={
            "markdown_doc": {
                "type": "string",
                "description": "The markdown document content to convert to TOML format",
            },
            "model": {
                "type": "string",
                "description": "The Gemini model to use for conversion",
                "default": "gemini-2.5-flash",
            },
        },
        required=["markdown_doc"],
    ),
)


def convert_markdown_to_toml_gemini(
    markdown_doc: str, model: str = "gemini-2.5-flash"
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
            ["gemini", "--model", model, "--prompt", prompt_with_args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error calling gemini: {e}")
        return f"#Error converting markdown\n# {str(e)}"


def convert_markdown_to_toml_claude_code(
    markdown_doc: str, model: str = CLAUDE_MODEL
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
            ["claude", "--model", model, "-p", prompt_with_args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error calling claude: {e}")
        return f"# Error converting markdown\n# {str(e)}"


def validate_toml(tomlfile: str) -> Tuple[bool, str, str]:
    """
    Validate a TOML file for syntax errors.
    Args:
        tomlfile: TOML content as string

    Returns:
        Tuple of (is_valid, tomlfile, list_of_errors)
        - is_valid: True if valid TOML, False otherwise
        - the original toml file
        - errors: Empty str if valide, list of error messages if invalid
    """

    print("Validating TOML File")

    try:
        tomllib.loads(tomlfile)
        return (True, tomlfile, "")
    except tomllib.TOMLDecodeError as e:
        return (False, tomlfile, str(e))

    except Exception as e:
        return (False, tomlfile, f"Unexpected error while parsing: {str(e)}")


def process_errors_claude(tomlfile: str, errors: str) -> str:
    """
    Process TOML content errors using Claude AI to generate fixes.

    Args:
        tomlfile: TOML file content as a string
        errors: Error description/messages to be fixed

    Returns:
        The fixed TOML content as a string

    Raises:
        subprocess.CalledProcessError: If Claude command fails
        ValueError: If Claude returns empty or invalid response
    """

    prompt = f"""
    You are a TOML configuration expert.
    Please fix the following TOML file based on the errors provided.

    Current TOML file content:
    {tomlfile}

    Errors to fix:
    {errors}

    Instructions:
    - Return ONLY the corrected TOML content
    - Fix all mentioned errors
    - Preserve all valid existing configuration
    - Ensure the output is valid TOML syntax
    - Do not include any explanations, just respond with the fixed TOMLas a string
    """

    try:
        result = subprocess.run(
            ["claude", "--model", CLAUDE_MODEL, "--prompt", prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error calling claude: {e}")
        return f"# Error converting markdown\n# {str(e)}"
