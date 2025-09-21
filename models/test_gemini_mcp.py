import pytest
from config import Config
from secret_manager import SecretManager
from models.gemini_mcp import GeminiMCP


@pytest.fixture
def gemini_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "gemini-2.5-flash"
    return GeminiMCP(config, secret_mgr, model)


@pytest.mark.asyncio
async def test_token_count_youtube(gemini_mcp):
    yt_url = "https://www.youtube.com/watch?v=4GiqzUHD5AA"
    token_count = await gemini_mcp.count_tokens_video(yt_url)
    print(f"Token count is: {token_count}")


async def test_youtube(gemini_mcp):
    yt_url = "https://www.youtube.com/watch?v=4GiqzUHD5AA"
    response = await gemini_mcp.analyze_video(yt_url)
    print(response)


def test_get_model_list(gemini_mcp):
    results = gemini_mcp.get_model_list()

    # Check that results is a list
    assert isinstance(results, list)
    assert len(results) > 0

    # Check structure of each model in results
    for model in results:
        assert isinstance(model, dict)
        assert "model_name" in model
        assert "token_window" in model

        # Verify we only get 2.0 and 2.5 models (as per filter)
        assert "2.0" in model["model_name"] or "2.5" in model["model_name"]

        print(f"{model['model_name']}: {model['token_window']:,} tokens")


def test_send_message(gemini_mcp):
    message = "Hello, world!"
    response = gemini_mcp.send_message(message)

    assert isinstance(response, dict)
    assert "candidates" in response
    assert len(response["candidates"]) > 0
    assert "content" in response["candidates"][0]
    assert "parts" in response["candidates"][0]["content"]

    print(f"Response: {response}")


def test_count_tokens(gemini_mcp):
    text = "Hello, world!"
    token_count = gemini_mcp.count_tokens(text)

    assert isinstance(token_count, int)
    assert token_count > 0

    print(f"Token count for '{text}': {token_count}")


def test_extract_text(gemini_mcp):
    message = "Say 'Hello, test!' and nothing else."
    response = gemini_mcp.send_message(message)
    extracted_text = gemini_mcp.extract_text(response)

    assert isinstance(extracted_text, str)
    assert len(extracted_text) > 0
    assert "Hello" in extracted_text

    print(f"Extracted text: {extracted_text}")
