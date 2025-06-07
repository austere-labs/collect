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
from bars import Bar, TimeFrameMatcher
from polygon.polygon import Polygon


mcp = FastMCP("URL Collector")


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
async def run_git_diff_review(
        to_file: str = "codereview", staged_only: bool = True):
    """
    Run code review on git diff output.

    Args:
        to_file: Directory name to write results to (default: "codereview")
        staged_only: If True, review only staged changes;
        if False, review all changes

    Returns:
        Summary of the code review results
    """
    reviewer = CodeReviewer(to_file)
    return await reviewer.review_diff_from_git(to_file, staged_only)


@mcp.tool()
async def fetch_urls(urls: List[str], ctx: Context = None) -> str:
    fetcher = Fetcher(ctx)
    merged_responses = await fetcher.fetch_urls(urls)
    return merged_responses


@mcp.tool()
async def fetch_url(url: str, ctx: Context = None) -> str:
    fetcher = Fetcher(ctx)
    return fetcher.get(url)


@mcp.tool()
async def get_docs(
        url: str, extract_value: str = None, ctx: Context = None) -> str:
    """
    If you provide a extract value, we will run the prompt below to provide
    a contextual prompt to extract the value that we are looking for in the
    web page.
    Otherwise we just go get the webpage.
    """
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "gemini-2.5-flash-preview-05-20"
    gemini = GeminiMCP(config, secret_mgr, model=model)

    if extract_value is None:
        fetcher = Fetcher(ctx)
        response = await fetcher.get(url)
        return response.text
    else:
        prompt_prefatory = f"""
        # Documentation Extraction Task

        Extract and format the documentation for: **{extract_value}**

        ## Instructions:
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


@mcp.prompt()
async def copy_clipboard_prompt(text: str) -> str:
    """
    I actually think the model can do this just fine without this prompt
    This lives here only as an example
    """
    return f"""
        # Use the instructions from {text} to create the text input for the
        mcp tool defined in Task 1.

        ## Task 1: Please use the mcp tool copy_clipboard

        ```python
        @mcp.tool()
        async def copy_clipboard(text: str):
            pyperclip.copy(text)
        ```
    """


@mcp.tool()
async def copy_clipboard(text: str):
    pyperclip.copy(text)


@mcp.tool()
def strip_html(html: str) -> str:
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
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    model = config.anthropic_model_sonnet
    anthropic_mcp = AnthropicMCP(
        config, secret_mgr, model)
    return anthropic_mcp.get_model_list()


@mcp.tool()
async def get_openai_model_list() -> List[str]:
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    openai_mcp = OpenAIMCP(config, secret_mgr, model="gpt-4o")
    return openai_mcp.get_model_list()


@mcp.tool()
async def get_xai_model_list() -> List[str]:
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    xai_mcp = XaiMCP(config, secret_mgr, model="grok-3-mini-fast-latest")
    return xai_mcp.get_model_list()


@mcp.tool()
async def get_gemini_model_list() -> List[str]:
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    gemini_mcp = GeminiMCP(config, secret_mgr, model="gemini-2.5-flash")
    return gemini_mcp.get_model_list()


@mcp.tool()
async def count_openai_tokens(text: str, model: str = "gpt-4") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


@mcp.tool()
async def count_anthropic_tokens(text: str) -> int:
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = config.anthropic_model_sonnet
    anthropic_mcp = AnthropicMCP(
        config, secret_mgr, model)
    return anthropic_mcp.count_tokens(text)


@mcp.tool()
async def count_gemini_tokens(text: str) -> int:
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    gemini_mcp = GeminiMCP(config, secret_mgr, model="gemini-2.0-flash")
    return gemini_mcp.count_tokens(text)


@mcp.tool()
async def count_grok_tokens(text: str) -> int:
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    xai_mcp = XaiMCP(config, secret_mgr, model="grok-3-fast-latest")
    return xai_mcp.count_tokens(text)


@mcp.tool()
async def use_polygon(url: str) -> List[Bar]:
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    api_key = secret_mgr.get_secret(config.polygon_api_key_path)
    pg = Polygon(config.polygon_base_url, api_key)

    # Parse URL first to validate format before making API call
    parsed_url = pg.parse_polygon_url(url)
    if parsed_url is None:
        raise ValueError(f"Invalid Polygon URL format: {url}")

    # Validate timeframe before making API call
    matcher = TimeFrameMatcher()
    timeframe = matcher.match(parsed_url["span"])
    if timeframe is None:
        raise ValueError(f"Unsupported timeframe: {parsed_url['span']}")

    # Make API call
    json_response = await pg.ohlvc_url(url)

    # Build bars
    symbol = parsed_url["symbol"]
    bars = pg.build_bars(json_response, symbol, timeframe)
    return bars


@mcp.tool()
async def generate_prompt(prompt: str, target_model: str = None) -> str:
    """
    Generate an improved prompt using Anthropic's experimental prompt tools API.

    Args:
        prompt: Task description or prompt text to optimize
        target_model: Optional target model name for optimization

    Returns:
        Generated prompt text from Anthropic's API
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

        # Build API request payload
        data = {"task": task_content}
        if target_model:
            data["target_model"] = target_model

        # Call generate_prompt API
        response = anthropic_mcp.generate_prompt(data)

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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
