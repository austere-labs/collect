import pytest

from collect import (
    fetch_urls,
    to_markdown,
    count_anthropic_tokens,
    count_gemini_tokens,
    count_openai_tokens,
    count_grok_tokens,
)

# The @pytest.mark.parametrize decorator runs the test function
#  test_empty_text_returns_zero three separate times, once for each
#  function in the list. Each time, it passes a different token-counting
#  function to the test as the func parameter.

#  This is useful for testing similar functionality across multiple
#  implementations without duplicating test code. In this case, it verifies
#   that all three token-counting functions return zero when given empty
#  text.


@pytest.mark.asyncio
async def test_openai_hello_token_count():
    result = await count_openai_tokens("hello", model="gpt-3.5-turbo")
    assert result == 1


@pytest.mark.parametrize(
    "func,text",
    [
        (count_openai_tokens, "Hello, world!"),
        (count_gemini_tokens, "Hello, Gemini!"),
        (count_anthropic_tokens, "Hello Claude"),
        (count_grok_tokens, "Hello Grok"),
    ],
)
@pytest.mark.asyncio
async def test_nonempty_text_returns_positive_int(func, text):
    n = await func(text)
    assert isinstance(n, int)
    assert n > 0


url1 = "https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md"
url2 = "https://modelcontextprotocol.io/llms-full.txt"


@pytest.mark.asyncio
async def test_fetch():
    """
    pytest test_collect.py::test_fetch -v -s
    """
    urls = [url1, url2]

    result = await fetch_urls(urls)
    markdown = to_markdown(result)

    anthropic__count_html = await count_anthropic_tokens(result)
    print(f"\n\n ---- ANTHROPIC:HTML {anthropic__count_html} ----\n")

    anthropic_count_markdown = await count_anthropic_tokens(markdown)
    print(f"\n\n ---- ANTHROPIC:Markdown {anthropic_count_markdown} ----\n")

    gemini_count_html = await count_gemini_tokens(result)
    print(f"\n\n ---- GEMINI:HTML: {gemini_count_html} ----\n")

    gemini_count_markdown = await count_gemini_tokens(markdown)
    print(f"\n\n ---- GEMINI:Markdown: {gemini_count_markdown} ----\n")

    openai_count_html = await count_openai_tokens(result)
    print(f"\n\n ---- OPENAI:HTML {openai_count_html} ----\n")

    openai_count_markdown = await count_openai_tokens(markdown)
    print(f"\n\n ---- OPENAI:Markdown {openai_count_markdown} ----\n")

    grok_count_html = await count_grok_tokens(result)
    print(f"\n\n ---- GROK:HTML {grok_count_html} ----\n")

    grok_count_markdown = await count_grok_tokens(markdown)
    print(f"\n\n ---- GROK:Markdown {grok_count_markdown} ----\n")
