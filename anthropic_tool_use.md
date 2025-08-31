# Anthropic Tool Use Implementation Guide

## Overview

This guide shows how to implement tool calling with Anthropic's Claude API using Pydantic models for type safety and structured responses.

## Pydantic Models

### Content Block Models

```python
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

# Union type for all possible content blocks
ContentBlock = Union[TextBlock, ToolUseBlock, ToolResultBlock]

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[ContentBlock]]
```

### Request/Response Models

```python
class AnthropicRequest(BaseModel):
    model: str
    max_tokens: int = Field(gt=0, le=4096)
    messages: List[Message] = Field(min_length=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Dict[str, Any]] = None

class AnthropicResponse(BaseModel):
    content: List[ContentBlock]
    id: str
    model: str
    role: Literal["assistant"]
    stop_reason: Optional[Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]]
    stop_sequence: Optional[str] = None
    usage: Dict[str, int]
```

## Tool Executor Implementation

### Class-Based Approach

```python
from typing import Dict, Any, Callable
import subprocess
import json

class ToolExecutor:
    def __init__(self):
        # Registry of available tools
        self.tools = {
            "convert_markdown_to_toml_gemini": self.convert_markdown_to_toml,
            "calculate_sum": self.calculate_sum,
            "file_reader": self.read_file,
            "web_search": self.web_search,
        }
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Main entry point for tool execution"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        try:
            # Call the appropriate tool function
            result = self.tools[tool_name](tool_input)
            return str(result)
        except Exception as e:
            raise RuntimeError(f"Tool {tool_name} failed: {str(e)}")
    
    def convert_markdown_to_toml(self, inputs: Dict[str, Any]) -> str:
        """Convert markdown to TOML using external tool"""
        markdown_doc = inputs.get("markdown_doc", "")
        
        try:
            # Call external gemini CLI tool
            result = subprocess.run(
                ["gemini", "--prompt", "convert to toml", "--input", markdown_doc],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Gemini tool failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Tool execution timed out")
        except FileNotFoundError:
            raise RuntimeError("Gemini CLI tool not found")
    
    def calculate_sum(self, inputs: Dict[str, Any]) -> float:
        """Simple calculation tool"""
        numbers = inputs.get("numbers", [])
        if not isinstance(numbers, list):
            raise ValueError("Expected 'numbers' to be a list")
        
        return sum(float(n) for n in numbers)
    
    def read_file(self, inputs: Dict[str, Any]) -> str:
        """Read file contents"""
        file_path = inputs.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise RuntimeError(f"File not found: {file_path}")
        except PermissionError:
            raise RuntimeError(f"Permission denied: {file_path}")
    
    def web_search(self, inputs: Dict[str, Any]) -> str:
        """Mock web search tool"""
        query = inputs.get("query", "")
        max_results = inputs.get("max_results", 5)
        
        # In real implementation, you'd call a search API
        return json.dumps({
            "query": query,
            "results": [
                {"title": f"Result {i}", "url": f"https://example.com/{i}"}
                for i in range(max_results)
            ]
        })
```

### Simple Function-Based Approach

```python
def execute_tool_func(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Simplified function-based approach"""
    tool_registry = {
        "convert_markdown_to_toml_gemini": convert_markdown_to_toml_gemini
    }
    
    if tool_name not in tool_registry:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    if tool_name == "convert_markdown_to_toml_gemini":
        markdown_doc = tool_input["markdown_doc"]
        model = tool_input.get("model", "gemini-2.5-flash")
        return tool_registry[tool_name](markdown_doc, model)
    
    # Add more tool handling as needed
    raise NotImplementedError(f"Tool {tool_name} not implemented")
```

## Complete Tool Calling Flow

### Basic Usage

```python
def handle_tool_calling_basic():
    """Basic tool calling implementation"""
    # 1. Send initial request with tools
    request = AnthropicRequest(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[Message(role="user", content="Convert this markdown to TOML")],
        tools=[markdown_to_toml_gemini_tool],
        tool_choice=ToolChoice(type="auto")
    )
    
    # 2. Get response from Anthropic
    response = anthropic_mcp.get(request)
    
    # 3. Check for tool use and execute
    for content in response.content:
        if hasattr(content, 'type') and content.type == 'tool_use':
            try:
                result = execute_tool_func(content.name, content.input)
                print(f"Tool result: {result}")
            except Exception as e:
                print(f"Tool execution failed: {str(e)}")
```

### Complete Conversation Flow

```python
def handle_anthropic_tool_calling():
    """Complete example of handling tool calling with Anthropic"""
    
    tool_executor = ToolExecutor()
    
    # After getting response with tool_use
    response = anthropic_mcp.get(request)
    
    for content in response.content:
        if hasattr(content, 'type') and content.type == 'tool_use':
            try:
                # Execute the tool
                result = tool_executor.execute_tool(content.name, content.input)
                
                # Create tool result message
                tool_result_message = Message(
                    role="user",
                    content=[
                        ToolResultBlock(
                            tool_use_id=content.id,
                            content=result,
                            is_error=False,
                            type="tool_result"
                        )
                    ]
                )
                
                # Continue conversation with tool result
                follow_up_messages = [
                    original_message,  # Original user message
                    Message(
                        role="assistant",
                        content=response.content  # Assistant's response with tool_use
                    ),
                    tool_result_message  # Tool execution result
                ]
                
                # Send follow-up request
                follow_up_request = AnthropicRequest(
                    model=model_name,
                    max_tokens=1024,
                    messages=follow_up_messages
                )
                
                final_response = anthropic_mcp.get(follow_up_request)
                return final_response
                
            except Exception as e:
                # Handle tool execution error
                error_message = Message(
                    role="user",
                    content=[
                        ToolResultBlock(
                            tool_use_id=content.id,
                            content=f"Tool execution failed: {str(e)}",
                            is_error=True,
                            type="tool_result"
                        )
                    ]
                )
                # Continue with error message...
    
    return response
```

## Key Implementation Points

1. **Tool Registry**: Maps tool names to functions for organized execution
2. **Error Handling**: Comprehensive error catching and re-raising with context
3. **Input Validation**: Validates required parameters before execution
4. **External Tools**: Shows subprocess execution for CLI tools with timeout protection
5. **Type Safety**: Proper Pydantic typing throughout the flow
6. **Conversation Flow**: Maintains proper message roles and content structure

## Testing Example

```python
def test_get_request(anthropic_mcp):
    markdown_file = read_file(".claude/commands/example.md")
    toml_prompt = f"""
    <INSTRUCTIONS>
    Please convert the the `markdown_file` to TOML format.
    </INSTRUCTIONS>
    {markdown_file}
    """
    message = Message(role="user", content=toml_prompt)

    req = AnthropicRequest(
        model=anthropic_mcp.model,
        max_tokens=1024,
        messages=[message],
        tools=[markdown_to_toml_gemini_tool],
        tool_choice=ToolChoice(type="auto")
    )

    resp = anthropic_mcp.get(req)
    for content in resp.content:
        if hasattr(content, 'type') and content.type == 'tool_use':
            try:
                result = execute_tool(content.name, content.input)
                print(result)
            except Exception as e:
                print(f"Tool call failed with: {str(e)}")
```

This implementation provides a robust foundation for tool calling with Anthropic's Claude API, with proper error handling, type safety, and extensible tool management.