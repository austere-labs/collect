import pytest
from config import Config
from secret_manager import SecretManager
from models.xai_mcp import XaiMCP


@pytest.fixture
def xai_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "grok-3-mini-fast-latest"
    return XaiMCP(config, secret_mgr, model)


def test_get_model_list(xai_mcp):
    results = xai_mcp.get_model_list()

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(model, str) for model in results)

    for model_name in results:
        print(model_name)


def test_send_message(xai_mcp):
    message = "Hello, world!"
    response = xai_mcp.send_message(message)

    assert isinstance(response, dict)
    assert "choices" in response
    assert "model" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]
    assert "content" in response["choices"][0]["message"]

    print(f"Response: {response}")


def test_count_tokens(xai_mcp):
    text = "Hello, world!"
    token_count = xai_mcp.count_tokens(text)

    assert isinstance(token_count, int)
    assert token_count > 0

    print(f"Token count for '{text}': {token_count}")


def test_extract_text(xai_mcp):
    message = "Say 'Hello, test!' and nothing else."
    response = xai_mcp.send_message(message)
    extracted_text = xai_mcp.extract_text(response)
    
    assert isinstance(extracted_text, str)
    assert len(extracted_text) > 0
    assert "Hello" in extracted_text
    
    print(f"Extracted text: {extracted_text}")
