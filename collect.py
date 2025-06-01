import os
import datetime
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
import json
import asyncio
import pyperclip

mcp = FastMCP("URL Collector")


@mcp.tool()
async def fetch_urls(urls: List[str], ctx: Context = None) -> str:
    fetcher = Fetcher(ctx)
    merged_responses = await fetcher.fetch_urls(urls)
    return merged_responses


@mcp.tool()
async def fetch_url(url: str, ctx: Context = None) -> str:
    fetcher = Fetcher(ctx)
    return fetcher.get_url(url)


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
        return response


@mcp.prompt()
async def copy_clipboard_prompt(text: str) -> str:
    """
    I actually think the model can do this just fine without this prompt
    This lives here only as an example
    """
    return f"""
        # Use the instructions from {text} to create the text input for the mcp tool defined in Task 1.

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
async def multi_model_code_review(output_dir: str, from_file: str = "diff.md"):
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    anthropic_model = config.anthropic_default_code_review_model
    gemini_model = config.gemini_default_code_review_model
    xai_model = config.xai_default_code_review_model
    openai_model = config.openai_default_code_review_model

    models = [
        anthropic_model,
        gemini_model,
        xai_model,
        openai_model,
    ]

    # Initialize MCP instances with default models
    gemini_mcp = GeminiMCP(config, secret_mgr, gemini_model)
    openai_mcp = OpenAIMCP(config, secret_mgr, openai_model)
    xai_mcp = XaiMCP(config, secret_mgr, xai_model)
    anthropic_mcp = AnthropicMCP(config, secret_mgr, anthropic_model)

    model_mcps = {
        gemini_model: gemini_mcp,
        openai_model: openai_mcp,
        xai_model: xai_mcp,
        anthropic_model: anthropic_mcp,
    }

    # Read content from file
    try:
        with open(from_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return {"error": f"File not found: {from_file}"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    async def call_model(model_name: str):

        try:
            start_time = datetime.now()
            iso_time = start_time.isoformat()

            # Send message to model
            mcp_instance = model_mcps[model_name]
            print(f"sending to --> {model_name} : at -> {iso_time}")
            response = mcp_instance.send_message(content, model=model_name)
            end_time = datetime.now()

            result = {
                "model": model_name,
                "actual_model": model_name,
                "timestamp": iso_time,
                "duration_seconds": (end_time - start_time).total_seconds(),
                "response": response,
                "success": True
            }

            # Save individual result to file
            safe_filename = model_name.replace('/', '_').replace(':', '_')
            filename = f"{safe_filename}_{
                start_time.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "file": filepath,
                "model": model_name,
                "duration": result["duration_seconds"],
            }

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }

            return error_result

    # Run all model calls concurrently
    print(f"Starting concurrent calls to {len(models)} models...")
    tasks = [call_model(model) for model in models]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Create summary
    successful_results = [
        r.get("response") for r in results
        if isinstance(r, dict) and r.get("success")
    ]

    failed_results = [r for r in results if isinstance(
        r, dict) and not r.get("success")]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "input_file": from_file,
        "output_directory": output_dir,
        "total_models": len(models),
        "successful": len(successful_results),
        "failed": len(failed_results),
        "models_requested": models,
        "available_models": list(model_mcps.keys()),
        "results": results,
        "total_input_tokens": sum(r.get("input_tokens", 0) for r in successful_results),
        "average_duration": sum(r.get("duration", 0) for r in successful_results) / len(successful_results) if successful_results else 0
    }

    # Save summary file
    summary_file = os.path.join(output_dir, f"summary_{
        datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


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

    gemini_mcp = GeminiMCP(config, secret_mgr, model="gemini-2.0-flash")
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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
