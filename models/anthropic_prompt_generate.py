from typing import List, Optional
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
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    service_tier: Optional[str] = None


class PromptGenerateResponse(BaseModel):
    """Response from Anthropic's prompt tools generate API."""

    messages: List[Message]
    """List of message objects that can be used directly in the Messages API.
    Typically includes a user message with the generated prompt text,
    and may include an assistant message with a prefill."""

    system: str = ""
    """Currently always empty string. May contain system prompts in future."""

    usage: UsageStats
    """Token usage statistics for the generation."""


# Example usage:
if __name__ == "__main__":
    # Example JSON response
    example_json = {
        "messages": [
            {
                "content": [
                    {
                        "text": "<generated prompt>",
                        "type": "text"
                    }
                ],
                "role": "user"
            }
        ],
        "system": "",
        "usage": {
            "input_tokens": 490,
            "output_tokens": 661
        }
    }

    # Parse into Pydantic model
    response = PromptGenerateResponse(**example_json)
    print(f"Generated prompt: {response.messages[0].content[0].text}")
    print(f"Input tokens: {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")
