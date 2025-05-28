import httpx
import pyperclip
from typing import List, Union
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

mcp = FastMCP("URL Collector")


@mcp.tool()
async def collect(
        urls: List[str], ctx: Context = None) -> Union[str, List[str]]:
    result_str = fetch_urls(urls, ctx)

    token_count = await count_anthropic_tokens(result_str)
    if token_count > 25000:
        return chunk_by_token_count(result_str)

    return result_str


async def chunk_by_token_count(
        text: str, max_tokens: int = 25000) -> List[str]:
    """
    Split text into chunks that are each under the specified token count.

    Args:
        text: The text to chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        List of text chunks, each under max_tokens
    """

    # If text is short enough, return as a single chunk
    token_count = await count_anthropic_tokens(text)
    if token_count <= max_tokens:
        return [text]

    # Split text into paragraphs as a starting point
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = await count_anthropic_tokens(paragraph + "\n\n")

        # If adding this paragraph would exceed the limit, start a new chunk
        if current_chunk_tokens + paragraph_tokens > max_tokens:
            # If the paragraph alone exceeds the limit, we split it further
            if paragraph_tokens > max_tokens:
                # Split by sentences or just characters if needed
                sentences = paragraph.split(". ")
                for sentence in sentences:
                    sentence_tokens = await count_anthropic_tokens(sentence + ". ")
                    if current_chunk_tokens + sentence_tokens > max_tokens:
                        if current_chunk:
                            chunks.append("".join(current_chunk))
                        current_chunk = [sentence + ". "]
                        current_chunk_tokens = sentence_tokens
                    else:
                        current_chunk.append(sentence + ". ")
                        current_chunk_tokens += sentence_tokens
            else:
                # Save the current chunk and start a new one
                chunks.append("".join(current_chunk))
                current_chunk = [paragraph + "\n\n"]
                current_chunk_tokens = paragraph_tokens
        else:
            # Add paragraph to current chunk
            current_chunk.append(paragraph + "\n\n")
            current_chunk_tokens += paragraph_tokens

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


async def fetch_urls(
        urls: List[str], ctx: Context = None) -> str:
    """
    Fetch content from multiple URLs and concatenate their responses.
    If token count exceeds 25000, content is split into chunks.

    Args:
        urls: List of URLs to fetch content from
        ctx: Optional context object for progress reporting

    Returns:
        Either concatenated content from all URLs as a string,
        or a list of content chunks if token count exceeds 25000
    """
    results = []

    async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True) as client:
        for i, url in enumerate(urls):
            if ctx:
                ctx.info(f"Fetching content from {url}")
                await ctx.report_progress(i, len(urls))

            try:
                response = await client.get(url)
                response.raise_for_status()

                results.append(f"\n\n--- Content from {url} --\n\n")
                results.append(response.text)

            except httpx.HTTPError as e:
                results.append(
                    f"\n\n --- Error fetching {url}: {str(e)} ---\n\n")
            except Exception as e:
                results.append(
                    f"\n\n--- error fetching {url}: {str(e)} ---\n\n")

    if ctx:
        ctx.info("all urls processed")
        await ctx.report_progress(len(urls), len(urls))

    content = "".join(results)

    # Copy original content to clipboard
    pyperclip.copy(content)

    # Otherwise return the original content
    return content


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
