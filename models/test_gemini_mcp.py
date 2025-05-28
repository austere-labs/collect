import pytest
from config import Config
from secret_manager import SecretManager
from models.gemini import GeminiMCP


@pytest.fixture
def gemini_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "gemini-2.0-flash"
    return GeminiMCP(config, secret_mgr, model)


def test_get_model_list(gemini_mcp):
    results = gemini_mcp.get_model_list()

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(model, str) for model in results)

    for model_name in results:
        print(model_name)


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