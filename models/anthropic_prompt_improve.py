from typing import List
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


class PromptImproveResponse(BaseModel):
    """Response from Anthropic's prompt tools improve API."""

    messages: List[Message]
    """List of message objects that can be used directly in the Messages API.
    Typically includes a user message with the improved prompt text,
    and an assistant message with a prefill to guide the model's response."""

    system: str = ""
    """Currently always empty string. May contain system prompts in future."""

    usage: List[UsageStats]
    """Token usage statistics for the improvement."""


# Example usage:
if __name__ == "__main__":
    # Example JSON response from the improve endpoint
    example_json = {
        "messages": [
            {
                "content": [
                    {
                        "text": "<improved prompt>",
                        "type": "text"
                    }
                ],
                "role": "user"
            },
            {
                "content": [
                    {
                        "text": "<assistant prefill>",
                        "type": "text"
                    }
                ],
                "role": "assistant"
            }
        ],
        "system": "",
        "usage": {
            "input_tokens": 490,
            "output_tokens": 661
        }
    }

    # Parse into Pydantic model
    response = PromptImproveResponse(**example_json)
    print(f"Improved prompt: {response.messages[0].content[0].text}")
    print(f"Assistant prefill: {response.messages[1].content[0].text}")
    print(f"Input tokens: {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")
