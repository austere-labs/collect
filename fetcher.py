from typing import List
from mcp.server.fastmcp import Context
import pyperclip
import httpx
from models.anthropic_mpc import AnthropicMCP


class Fetcher:
    def __init__(self, ctx: Context = None) -> None:
        self.ctx = ctx

    async def fetch_url(self, url: str) -> str:
        """
        Fetch content from a single URL.

        Args:
            url: URL to fetch content from

        Returns:
            Content from the URL as a string
        """

        async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text

                return content

            except httpx.HTTPError as e:
                return f"Error fetching {url}: {str(e)}"
            except Exception as e:
                return f"Error fetching {url}: {str(e)}"

    async def fetch_urls(self, urls: List[str]) -> str:
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
                if self.ctx:
                    self.ctx.info(f"Fetching content from {url}")
                    await self.ctx.report_progress(i, len(urls))

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

        if self.ctx:
            self.ctx.info("all urls processed")
            await self.ctx.report_progress(len(urls), len(urls))

        content = "".join(results)

        # Copy original content to clipboard
        pyperclip.copy(content)

        # Otherwise return the original content
        return content

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
        anthropic_mcp = AnthropicMCP()
        token_count = await anthropic_mcp.count_tokens(text, None)
        if token_count <= max_tokens:
            return [text]

        # Split text into paragraphs as a starting point
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = await anthropic_mcp.count_tokens(
                paragraph + "\n\n", None)

            # If adding this paragraph would exceed the limit,
            # start a new chunk
            if current_chunk_tokens + paragraph_tokens > max_tokens:
                # If the paragraph alone exceeds the limit, we split it further
                if paragraph_tokens > max_tokens:
                    # Split by sentences or just characters if needed
                    sentences = paragraph.split(". ")
                    for sentence in sentences:
                        sentence_tokens = await anthropic_mcp.count_tokens(
                            sentence + ". ", None)
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
