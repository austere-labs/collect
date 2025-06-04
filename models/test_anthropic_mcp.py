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


def test_generate_prompt(anthropic_mcp):
    """Test the generate_prompt method with a simple task."""
    data = {
        "task": "Write a helpful assistant prompt for answering coding questions"
    }

    response = anthropic_mcp.generate_prompt(data)

    # Test response structure
    assert hasattr(response, 'messages')
    assert hasattr(response, 'system')
    assert hasattr(response, 'usage')

    # Test messages
    assert isinstance(response.messages, list)
    assert len(response.messages) > 0

    # Test first message
    first_message = response.messages[0]
    assert hasattr(first_message, 'role')
    assert hasattr(first_message, 'content')
    assert first_message.role in ['user', 'assistant']
    assert isinstance(first_message.content, list)
    assert len(first_message.content) > 0

    # Test content
    content = first_message.content[0]
    assert hasattr(content, 'text')
    assert hasattr(content, 'type')
    assert content.type == 'text'
    assert isinstance(content.text, str)
    assert len(content.text) > 0

    # Test usage stats
    assert hasattr(response.usage, 'input_tokens')
    assert hasattr(response.usage, 'output_tokens')
    assert isinstance(response.usage.input_tokens, int)
    assert isinstance(response.usage.output_tokens, int)
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0

    print(f"Generated prompt: {content.text[:100]}...")
    print(f"Usage: {response.usage.input_tokens} input, {
          response.usage.output_tokens} output tokens")


def test_improve_prompt(anthropic_mcp):
    """Test the improve_prompt method with a simple prompt."""
    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Tell me about Python programming"
                    }
                ]
            }
        ],
        "system": "You are a helpful programming instructor",
        "feedback": "Make this prompt more specific for a beginner",
        "target_model": "claude-3-7-sonnet-20250219"
    }

    response = anthropic_mcp.improve_prompt(data)

    # Test response structure
    assert hasattr(response, 'messages')
    assert hasattr(response, 'system')
    assert hasattr(response, 'usage')

    # Test messages - should have both user and assistant messages
    assert isinstance(response.messages, list)
    assert len(response.messages) >= 2

    # Test user message (improved prompt)
    user_message = response.messages[0]
    assert user_message.role == 'user'
    assert isinstance(user_message.content, list)
    assert len(user_message.content) > 0

    # Find the non-empty content in user message
    user_content = None
    for content in user_message.content:
        if content.text:
            user_content = content
            break

    assert user_content is not None, "No non-empty content found in user message"
    assert hasattr(user_content, 'text')
    assert hasattr(user_content, 'type')
    assert user_content.type == 'text'
    assert isinstance(user_content.text, str)
    assert len(user_content.text) > 0

    # Test assistant message (prefill)
    assistant_message = response.messages[1]
    assert assistant_message.role == 'assistant'
    assert isinstance(assistant_message.content, list)
    assert len(assistant_message.content) > 0

    assistant_content = assistant_message.content[0]
    assert hasattr(assistant_content, 'text')
    assert hasattr(assistant_content, 'type')
    assert assistant_content.type == 'text'
    assert isinstance(assistant_content.text, str)
    assert len(assistant_content.text) > 0

    # Test usage stats (as list according to actual API response)
    assert isinstance(response.usage, list)
    assert len(response.usage) > 0

    usage = response.usage[0]
    assert hasattr(usage, 'input_tokens')
    assert hasattr(usage, 'output_tokens')
    assert isinstance(usage.input_tokens, int)
    assert isinstance(usage.output_tokens, int)
    assert usage.input_tokens > 0
    assert usage.output_tokens > 0

    print(f"Improved prompt: {user_content.text[:100]}...")
    print(f"Assistant prefill: {assistant_content.text[:50]}...")
    print(f"Usage: {usage.input_tokens} input, {
          usage.output_tokens} output tokens")


def test_templatize_prompt(anthropic_mcp):
    """Test the templatize_prompt method with a simple prompt."""
    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Translate hello to German"
                    }
                ]
            }
        ],
        "system": "You are an English to German translator"
    }

    response = anthropic_mcp.templatize_prompt(data)

    # Test response structure
    assert hasattr(response, 'messages')
    assert hasattr(response, 'system')
    assert hasattr(response, 'usage')
    assert hasattr(response, 'variable_values')

    # Test messages
    assert isinstance(response.messages, list)
    assert len(response.messages) > 0

    # Test first message
    first_message = response.messages[0]
    assert hasattr(first_message, 'role')
    assert hasattr(first_message, 'content')
    assert first_message.role == 'user'
    assert isinstance(first_message.content, list)
    assert len(first_message.content) > 0

    # Test content
    content = first_message.content[0]
    assert hasattr(content, 'text')
    assert hasattr(content, 'type')
    assert content.type == 'text'
    assert isinstance(content.text, str)
    assert len(content.text) > 0
    # Check for template variables
    assert '{{' in content.text and '}}' in content.text

    # Test system prompt
    assert isinstance(response.system, str)
    # System prompt should also contain template variables
    assert '{{' in response.system and '}}' in response.system

    # Test variable_values
    assert isinstance(response.variable_values, dict)
    assert len(response.variable_values) > 0
    # Check for expected variables based on the example
    assert any(key in response.variable_values for key in ['TARGET_LANGUAGE', 'WORD_TO_TRANSLATE'])

    # Test usage stats (as list according to actual API response)
    assert isinstance(response.usage, list)
    assert len(response.usage) > 0
    
    usage = response.usage[0]
    assert hasattr(usage, 'input_tokens')
    assert hasattr(usage, 'output_tokens')
    assert isinstance(usage.input_tokens, int)
    assert isinstance(usage.output_tokens, int)
    assert usage.input_tokens > 0
    assert usage.output_tokens > 0

    print(f"Templated prompt: {content.text[:100]}...")
    print(f"System prompt: {response.system[:100]}...")
    print(f"Variables: {response.variable_values}")
    print(f"Usage: {usage.input_tokens} input, {
          usage.output_tokens} output tokens")
