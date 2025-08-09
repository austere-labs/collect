from typing import List
from mcp.server.fastmcp import FastMCP, Context
import tiktoken
import markdownify
import readabilipy.simple_json
from html_to_markdown import convert_to_markdown
from bs4 import BeautifulSoup
from secret_manager import SecretManager
from config import Config
from models.anthropic_mpc import AnthropicMCP
from models.openai_mpc import OpenAIMCP
from models.xai_mcp import XaiMCP
from models.gemini_mcp import GeminiMCP
from fetcher import Fetcher
import pyperclip
from reviewer.code_review import CodeReviewer
import subprocess
import atexit
import time

mcp = FastMCP("Collect")


@mcp.tool()
async def run_code_review(from_file: str, to_file: str = "codereview"):
    """
    Run code review on a diff file using multiple LLM models.

    Args:
        from_file: Path to the file containing the diff/code to review
        to_file: Directory name to write results to (default: "codereview")

    Returns:
        Summary of the code review results
    """
    reviewer = CodeReviewer(to_file)
    return await reviewer.review_code(from_file, to_file)


@mcp.tool()
async def run_git_diff_review(to_file: str = "codereview", staged_only: bool = True):
    """
    Run code review on git diff output.

    Args:
        to_file: Directory name to write results to(default: "codereview")
        staged_only: If True, review only staged changes;
        if False, review all changes

    Returns:
        Summary of the code review results
    """
    reviewer = CodeReviewer(to_file)
    return await reviewer.review_diff_from_git(to_file, staged_only)


@mcp.tool()
async def fetch_urls(urls: List[str], ctx: Context = None) -> str:
    """
    Fetch content from multiple URLs concurrently and merge the responses.

    Use this tool when you need to:
    - Retrieve content from multiple web pages at once
    - Compare information across multiple sources
    - Gather data from several API endpoints simultaneously
    - Fetch related pages in parallel for efficiency

    Args:
        urls: List of URLs to fetch content from
        ctx: MCP context(automatically provided)

    Returns:
        Merged content from all URLs as a single string

    Example:
        fetch_urls(["https://api.example.com/users",
                   "https://api.example.com/posts"])
    """
    fetcher = Fetcher(ctx)
    merged_responses = await fetcher.fetch_urls(urls)
    return merged_responses


@mcp.tool()
async def fetch_url(url: str, ctx: Context = None) -> str:
    """
    Fetch raw content from a single URL.

    Use this tool when you need to:
    - Retrieve raw HTML/JSON from a web page or API
    - Get unprocessed content for custom parsing
    - Access web resources programmatically
    - Fetch data before converting to markdown

    Args:
        url: The URL to fetch content from
        ctx: MCP context(automatically provided)

    Returns:
        Raw content from the URL(HTML, JSON, or plain text)

    Note: For documentation extraction, consider using get_docs instead.
          For markdown conversion, use to_markdown on the result.
    """
    fetcher = Fetcher(ctx)
    return fetcher.get(url)


@mcp.tool()
async def get_docs(url: str, extract_value: str = None, ctx: Context = None) -> str:
    """
    Fetch and extract specific documentation content from web pages.

    Use this tool when users need to:
    - Extract specific sections from documentation websites
    - Get targeted information from technical docs
    - Retrieve API documentation for specific methods/classes
    - Pull configuration examples from documentation
    - Find specific topics within large documentation sites

    Args:
        url: The URL of the documentation page to fetch
        extract_value: Optional. Specific section/topic to extract(e.g., "authentication",
                      "API endpoints", "installation guide"). If not provided, returns
                      the entire page content.
        ctx: MCP context(automatically provided)

    Returns:
        Extracted documentation content as markdown. If extract_value is specified,
        uses Gemini AI to intelligently extract only the relevant section.

    Examples:
        - get_docs("https://docs.python.org/3/", "datetime module")
        - get_docs("https://fastapi.tiangolo.com/", "dependency injection")
        - get_docs("https://react.dev/", "useEffect hook")
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "gemini-2.5-flash-preview-05-20"
    gemini = GeminiMCP(config, secret_mgr, model=model)

    if extract_value is None:
        fetcher = Fetcher(ctx)
        response = await fetcher.get(url)
        return response
    else:
        prompt_prefatory = f"""
        # Documentation Extraction Task

        Extract and format the documentation for: **{extract_value} **

        # Instructions:
        - Focus specifically on the requested section/topic
        - Include code examples, parameters, and usage details if present
        - Maintain original formatting and structure
        - If the exact section isn't found, extract the most relevant related content
        - Return only the extracted documentation content, no meta-commentary

        ## Content to extract: {extract_value}
        """

        prompt = prompt_prefatory + "\n\n"
        response = await gemini.build_prompt_from_url(url, prompt, ctx)
        return response.strip()


@mcp.tool()
async def copy_clipboard(text: str) -> str:
    """
    Copy text to the system clipboard.

    Use this tool when users need to:
    - Copy generated code snippets to clipboard
    - Save formatted text for pasting elsewhere
    - Copy API keys, URLs, or configuration values
    - Transfer content between applications

    Args:
        text: The text content to copy to clipboard

    Note: The text will replace any existing clipboard content.
    """
    pyperclip.copy(text)


@mcp.tool()
def strip_html(html: str) -> str:
    """
    Remove all HTML tags and return plain text content.

    Use this tool when you need to:
    - Extract plain text from HTML pages
    - Remove formatting and tags from web content
    - Clean HTML for text analysis
    - Prepare content for non-HTML processing

    Args:
        html: Raw HTML string to process

    Returns:
        Plain text with all HTML tags removed

    Note: This removes ALL formatting. For readable formatting, use to_markdown instead.
    """
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text()


@mcp.tool()
def to_markdown(html: str) -> str:
    """Extract and convert HTML content to markdown using markdownify
    and readabilipy

    Args:
        html: Raw HTML retrieved from fetch_url or fetch_urls

    Returns:
        Simplified markdown

    """
    html_to_json = readabilipy.simple_json.simple_json_from_html_string(
        html,
        use_readability=True,
    )
    if not html_to_json["content"]:
        return "<error>Page failed to be simplified from HTML to json</error>"

    return markdownify.markdownify(
        html_to_json["content"],
        heading_style=markdownify.ATX,
    )


def html_to_markdown(html: str) -> str:
    """This uses html-to-markdown library instead of markdownify

    Args:
        html: Raw HTML retrieved from fetch_url or fetch_urls

    Returns:
        Simplified markdown as a str
    """

    return convert_to_markdown(
        html,
        heading_style="atx",
    )


@mcp.tool()
async def get_anthropic_model_list() -> List[str]:
    """
    Get the list of available Anthropic Claude models.

    Use this tool when you need to:
    - Check which Claude models are available
    - Verify model names before using them
    - List Anthropic's current model offerings
    - Help users choose between Claude models

    Returns:
        List of available Anthropic model names (e.g., ["claude-3-opus", "claude-3-sonnet"])
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    model = config.anthropic_model_sonnet
    anthropic_mcp = AnthropicMCP(config, secret_mgr, model)
    return anthropic_mcp.get_model_list()


@mcp.tool()
async def get_openai_model_list() -> List[str]:
    """
    Get the list of available OpenAI models.

    Use this tool when you need to:
    - Check which GPT models are available
    - Verify OpenAI model names
    - List current OpenAI offerings
    - Help users choose between GPT models

    Returns:
        List of available OpenAI model names (e.g., ["gpt-4", "gpt-3.5-turbo"])
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    openai_mcp = OpenAIMCP(config, secret_mgr, model="gpt-4o")
    return openai_mcp.get_model_list()


@mcp.tool()
async def get_xai_model_list() -> List[str]:
    """
    Get the list of available XAI (Grok) models.

    Use this tool when you need to:
    - Check which Grok models are available
    - Verify XAI model names
    - List current Grok offerings
    - Help users choose between Grok models

    Returns:
        List of available XAI model names (e.g., ["grok-3", "grok-3-mini"])
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    xai_mcp = XaiMCP(config, secret_mgr, model="grok-3-mini-fast-latest")
    return xai_mcp.get_model_list()


@mcp.tool()
async def get_gemini_model_list() -> List[dict]:
    """
    Get the list of available Google Gemini models
    (filtered for 2.0 and 2.5 versions).

    Use this tool when you need to:
    - Check which Gemini models are available with their token limits
    - Verify Google AI model names and capabilities
    - List current Gemini 2.0 and 2.5 offerings
    - Help users choose between Gemini models based on token capacity

    Returns:
        List of model dictionaries sorted by token limit (highest first),
        each containing:
        - model_name: The model identifier (e.g., "gemini-2.5-flash")
        - token_window: Input token limit (e.g., 1048576)

    Example return:
        [
            {"model_name": "gemini-2.5-flash", "token_window": 1048576},
            {"model_name": "gemini-2.0-flash", "token_window": 1048576},
            {"model_name": "gemini-2.5-pro", "token_window": 1048576}
        ]
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    gemini_mcp = GeminiMCP(config, secret_mgr, model="gemini-2.5-flash")
    return gemini_mcp.get_model_list()


@mcp.tool()
async def count_openai_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using OpenAI's tiktoken tokenizer.

    Use this tool when you need to:
    - Check if content fits within OpenAI model limits
    - Estimate API costs for OpenAI models
    - Split content to fit token windows
    - Optimize prompts for token efficiency

    Args:
        text: The text to count tokens for
        model: OpenAI model name (default: "gpt-4")

    Returns:
        Number of tokens in the text for the specified model
    """
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


@mcp.tool()
async def count_anthropic_tokens(text: str) -> int:
    """
    Count tokens in text using Anthropic's tokenizer.

    Use this tool when you need to:
    - Check if content fits within Claude model limits
    - Estimate API costs for Anthropic models
    - Split content for Claude's context window
    - Optimize prompts for Claude

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens in the text for Anthropic models
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = config.anthropic_model_sonnet
    anthropic_mcp = AnthropicMCP(config, secret_mgr, model)
    return anthropic_mcp.count_tokens(text)


@mcp.tool()
async def count_gemini_tokens(text: str) -> int:
    """
    Count tokens in text using Google Gemini's tokenizer.

    Use this tool when you need to:
    - Check if content fits within Gemini model limits
    - Estimate API costs for Google AI models
    - Split content for Gemini's context window
    - Optimize prompts for Gemini

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens in the text for Gemini models
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    gemini_mcp = GeminiMCP(config, secret_mgr, model="gemini-2.0-flash")
    return gemini_mcp.count_tokens(text)


@mcp.tool()
async def count_grok_tokens(text: str) -> int:
    """
    Count tokens in text using XAI Grok's tokenizer.

    Use this tool when you need to:
    - Check if content fits within Grok model limits
    - Estimate API costs for XAI models
    - Split content for Grok's context window
    - Optimize prompts for Grok

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens in the text for Grok models
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    xai_mcp = XaiMCP(config, secret_mgr, model="grok-3-fast-latest")
    return xai_mcp.count_tokens(text)


@mcp.tool()
async def generate_prompt(prompt: str, target_model: str = None) -> str:
    """
    Generate an optimized AI prompt using Anthropic's experimental prompt engineering API.

    This tool leverages Anthropic's closed research preview API to automatically create
    high-quality, structured prompts from simple task descriptions. The API analyzes
    your input and generates professional-grade prompts optimized for Claude models.

    Use this tool when you need to:
    - Transform simple ideas into comprehensive AI prompts
    - Create structured prompts for specific tasks or roles
    - Optimize prompts for better AI responses
    - Generate consistent prompt templates for repeated use
    - Improve prompt clarity and effectiveness

    Args:
        prompt: A brief description of what you want the AI to do.
                Can be as simple as a role description or task summary.
                Examples:
                - "a helpful programming assistant"
                - "a chef for meal planning"
                - "a technical documentation writer"
                - "analyze code for security vulnerabilities"
        target_model: Optional. The specific model to optimize for (e.g., "claude-3-opus").
                     If not specified, generates a general-purpose prompt.

    Returns:
        A professionally crafted prompt ready for use with Claude or other AI models.
        The generated prompt includes appropriate context, instructions, and structure
        to maximize response quality.

    Raises:
        ValueError: If the prompt is empty or only contains whitespace
        RuntimeError: If the API call fails or returns an unexpected response

    Example:
        >>> result = await generate_prompt("a Python code reviewer")
        >>> print(result)
        "You are an expert Python code reviewer with deep knowledge..."

    Note:
        This uses Anthropic's experimental "prompt-tools" API which requires special
        access. The API is in closed research preview and may change without notice.
    """
    try:
        # Validate input
        task_content = prompt.strip()
        if not task_content:
            raise ValueError("Prompt cannot be empty")

        # Set up Anthropic MCP client
        config = Config()
        secret_mgr = SecretManager(config.project_id)
        anthropic_mcp = AnthropicMCP(
            config, secret_mgr, config.anthropic_model_sonnet)

        # Call generate_prompt API with new signature
        response = anthropic_mcp.generate_prompt(task_content, target_model)

        # Extract the generated prompt text from the response
        if response.messages and response.messages[0].content:
            return response.messages[0].content[0].text
        else:
            raise ValueError("No prompt generated in response")

    except ValueError:
        # Re-raise ValueError (like empty prompt) without wrapping
        raise
    except Exception as e:
        raise RuntimeError(f"Error generating prompt: {str(e)}")


def main():
    # Start the API server in the background
    api_process = None
    try:
        # Launch API server as subprocess
        api_process = subprocess.Popen(
            ["uv", "run", "api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for API to initialize
        time.sleep(2)
        
        # Verify successful startup
        if api_process.poll() is not None:
            # Process ended unexpectedly
            stderr = api_process.stderr.read()
            print(f"API server failed to start: {stderr}")
        else:
            print(f"API server started with PID: {api_process.pid}")
            
            # Register cleanup handler
            def cleanup_api():
                if api_process and api_process.poll() is None:
                    print("Shutting down API server...")
                    api_process.terminate()
                    try:
                        api_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        api_process.kill()
            
            atexit.register(cleanup_api)
    
    except Exception as e:
        print(f"Failed to start API server: {e}")
    
    # Continue with MCP server startup
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
