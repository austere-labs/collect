from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any, Union


class TextBlock(BaseModel):
    text: str
    type: Literal["text"]


class ToolUseBlock(BaseModel):
    id: str
    name: str  # name of the function to call
    input: Dict[str, Any]  # arguments for the function
    type: Literal["tool_use"]


class ToolResultBlock(BaseModel):
    tool_use_id: str
    content: str  # result of the tool execution
    is_error: Optional[bool] = False  # indicate if the tool exec failed
    type: Literal["tool_result"]


ContentBlock = Union[TextBlock, ToolUseBlock, ToolResultBlock]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[ContentBlock]]


class Thinking(BaseModel):
    type: Literal["enabled"] = "enabled"
    budget_tokens: int = Field(
        ge=1024, description="Minimum 1024 tokens for thinking budget"
    )


class ToolInputSchema(BaseModel):
    type: Literal["object"] = "object"
    properties: Dict[str, Any]
    required: Optional[List[str]] = None


class Tool(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    input_schema: ToolInputSchema


class ToolChoice(BaseModel):
    type: Literal["auto", "any", "tool", "none"]
    disable_parallel_tool_use: Optional[bool] = False


class AnthropicRequest(BaseModel):
    model: str
    max_tokens: int = Field(gt=0, le=4096)
    messages: List[Message] = Field(min_length=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    thinking: Optional[Thinking] = None
    stream: Optional[bool] = False
    system: Optional[str] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[ToolChoice] = None


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnthropicResponse(BaseModel):
    content: List[ContentBlock]
    id: str
    model: str
    role: Literal["assistant"]
    stop_reason: Optional[
        Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]
    ]
    stop_sequence: Optional[str] = None
    usage: Usage
