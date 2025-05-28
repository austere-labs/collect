import pytest
from config import Config
from secret_manager import SecretManager
from models.openai import OpenAIMCP


@pytest.fixture
def openai_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    model = "gpt-4o"
    return OpenAIMCP(config, secret_mgr, model)


def test_get_model_list(openai_mcp):
    results = openai_mcp.get_model_list()

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(model, str) for model in results)

    for model_name in results:
        print(model_name)


def test_send_message(openai_mcp):
    message = "Hello, world!"
    response = openai_mcp.send_message(message)

    assert isinstance(response, dict)
    assert "choices" in response
    assert "model" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]
    assert "content" in response["choices"][0]["message"]

    print(f"Response: {response}")


def test_count_tokens(openai_mcp):
    text = "Hello, world!"
    token_count = openai_mcp.count_tokens(text)

    assert isinstance(token_count, int)
    assert token_count > 0

    print(f"Token count for '{text}': {token_count}")