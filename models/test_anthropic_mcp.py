import pytest
from config import Config
from secret_manager import SecretManager
from models.anthropic_mpc import AnthropicMCP


@pytest.fixture
def anthropic_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = config.anthropic_model_sonnet
    return AnthropicMCP(config, secret_mgr, model)


def test_get_model_list(anthropic_mcp):
    results = anthropic_mcp.get_model_list()

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(model, str) for model in results)

    for model_name in results:
        print(model_name)


def test_send_message(anthropic_mcp):
    message = "Hello, world!"
    response = anthropic_mcp.send_message(message)

    assert isinstance(response, dict)
    assert "content" in response
    assert "model" in response
    assert response["model"] == anthropic_mcp.config.anthropic_model_sonnet

    print(f"Response: {response}")


def test_extract_text(anthropic_mcp):
    message = "Say 'Hello, test!' and nothing else."
    response = anthropic_mcp.send_message(message)
    extracted_text = anthropic_mcp.extract_text(response)
    
    assert isinstance(extracted_text, str)
    assert len(extracted_text) > 0
    assert "Hello" in extracted_text
    
    print(f"Extracted text: {extracted_text}")
