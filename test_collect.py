import pytest

from collect import (
    count_anthropic_tokens,
    count_gemini_tokens,
    count_openai_tokens,
    count_grok_tokens,
    get_docs,
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


@pytest.mark.asyncio
async def test_get_docs_with_extract_value():
    url = "https://docs.python.org/3/library/json.html"
    extract_value = "json.dumps"

    result = await get_docs(url, extract_value)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "json.dumps" in result.lower()

    print(f"Extracted docs for {extract_value}:")
    print(result[:500] + "..." if len(result) > 500 else result)


@pytest.mark.asyncio
async def test_get_docs_without_extract_value():
    url = "https://docs.python.org/3/library/json.html"

    result = await get_docs(url)

    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain raw HTML content when no extraction is performed
    assert "html" in result.lower() or "json" in result.lower()

    print(f"Raw content length: {len(result)}")
    print(result[:200] + "..." if len(result) > 200 else result)
