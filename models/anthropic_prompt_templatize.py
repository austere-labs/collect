from typing import List, Dict
from pydantic import BaseModel


class MessageContent(BaseModel):
    """Content within a message."""

    text: str
    type: str = "text"


class Message(BaseModel):
    """Message object in the response."""

    role: str  # "user" or "assistant"
    content: List[MessageContent]


class UsageStats(BaseModel):
    """Token usage statistics."""

    input_tokens: int
    output_tokens: int


class PromptTemplatizeResponse(BaseModel):
    """Response from Anthropic's prompt tools templatize API."""

    messages: List[Message]
    """List of message objects with templated variables."""

    system: str = ""
    """System prompt with templated variables."""

    usage: List[UsageStats]
    """Token usage statistics for the templatization."""

    variable_values: Dict[str, str]
    """Dictionary mapping template variable names to their extracted values."""


# Example usage:
if __name__ == "__main__":
    # Example JSON response from the templatize endpoint
    example_json = {
        "messages": [
            {
                "content": [
                    {
                        "text": "Translate {{WORD_TO_TRANSLATE}} to {{TARGET_LANGUAGE}}",
                        "type": "text",
                    }
                ],
                "role": "user",
            }
        ],
        "system": "You are a professional English to {{TARGET_LANGUAGE}} translator",
        "usage": [{"input_tokens": 490, "output_tokens": 661}],
        "variable_values": {"TARGET_LANGUAGE": "German", "WORD_TO_TRANSLATE": "hello"},
    }

    # Parse into Pydantic model
    response = PromptTemplatizeResponse(**example_json)
    print(f"Templated prompt: {response.messages[0].content[0].text}")
    print(f"System prompt: {response.system}")
    print(f"Variables: {response.variable_values}")
    print(f"Input tokens: {response.usage[0].input_tokens}")
    print(f"Output tokens: {response.usage[0].output_tokens}")
