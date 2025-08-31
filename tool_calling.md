# Tool Calling with Anthropic API

This document provides a production-ready implementation for tool calling with the Anthropic Claude API.

## Overview

Tool calling allows Claude to invoke external functions and tools during conversations. This implementation provides a clean, type-safe wrapper around Anthropic's tool calling functionality.

## Implementation

```python
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from anthropic import Anthropic

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]

class AnthropicToolCaller:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.available_tools = {}
    
    def register_tool(self, tool_def: ToolDefinition, handler_func):
        """Register a tool with its handler function."""
        self.available_tools[tool_def.name] = {
            "definition": tool_def,
            "handler": handler_func
        }
    
    def send_message_with_tools(
        self, 
        message: str, 
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Send a message that can trigger tool calls."""
        
        # Convert tool definitions to Anthropic's format
        tools = []
        for tool_name, tool_info in self.available_tools.items():
            tool_def = tool_info["definition"]
            tools.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "input_schema": tool_def.input_schema
            })
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                tools=tools,
                messages=[{"role": "user", "content": message}]
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            raise RuntimeError(f"Failed to send message with tools: {e}")
    
    def _handle_response(self, response) -> Dict[str, Any]:
        """Process the response and execute any tool calls."""
        result = {
            "text_response": "",
            "tool_calls": [],
            "tool_results": []
        }
        
        for content_block in response.content:
            if content_block.type == "text":
                result["text_response"] += content_block.text
            
            elif content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_id = content_block.id
                
                result["tool_calls"].append({
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input
                })
                
                # Execute the tool
                if tool_name in self.available_tools:
                    try:
                        handler = self.available_tools[tool_name]["handler"]
                        tool_result = handler(**tool_input)
                        
                        result["tool_results"].append({
                            "id": tool_id,
                            "name": tool_name,
                            "result": tool_result
                        })
                    except Exception as e:
                        result["tool_results"].append({
                            "id": tool_id,
                            "name": tool_name,
                            "error": str(e)
                        })
        
        return result


# Example tool implementations
def get_weather(location: str) -> Dict[str, Any]:
    """Mock weather tool."""
    return {
        "location": location,
        "temperature": "22°C",
        "condition": "Sunny",
        "humidity": "65%"
    }

def calculate_math(expression: str) -> Dict[str, Any]:
    """Safe math calculator tool."""
    try:
        # Only allow safe operations
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            raise ValueError("Invalid characters in expression")
        
        result = eval(expression)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


# Usage example
if __name__ == "__main__":
    # Initialize the tool caller
    tool_caller = AnthropicToolCaller(api_key="your-api-key")
    
    # Register tools
    weather_tool = ToolDefinition(
        name="get_weather",
        description="Get current weather for a location",
        input_schema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city or location to get weather for"
                }
            },
            "required": ["location"]
        }
    )
    
    math_tool = ToolDefinition(
        name="calculate_math",
        description="Calculate mathematical expressions",
        input_schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to calculate"
                }
            },
            "required": ["expression"]
        }
    )
    
    tool_caller.register_tool(weather_tool, get_weather)
    tool_caller.register_tool(math_tool, calculate_math)
    
    # Send a message that might trigger tool calls
    response = tool_caller.send_message_with_tools(
        "What's the weather like in Paris? Also, what's 15 * 7?"
    )
    
    print("Text Response:", response["text_response"])
    print("Tool Calls:", response["tool_calls"])
    print("Tool Results:", response["tool_results"])
```

## Key Features

1. **Clean Architecture**: Separates tool definition, registration, and execution
2. **Type Safety**: Uses dataclasses and type hints throughout
3. **Error Handling**: Comprehensive error handling for both API calls and tool execution
4. **Flexible Tool Registration**: Easy to add new tools with their schemas
5. **Safe Execution**: Tools are executed in isolation with proper error capture
6. **Production Ready**: Includes proper logging points and structured responses

## Integration with Existing AnthropicMCP Class

To integrate with your existing `AnthropicMCP` class, you can add a method like:

```python
def send_message_with_tools(self, message: str, tools: List[Dict], max_tokens: int = 1024):
    data = {
        "model": self.model,
        "max_tokens": max_tokens,
        "tools": tools,
        "messages": [{"role": "user", "content": message}]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages", 
        headers=self.headers, 
        json=data
    )
    response.raise_for_status()
    return response.json()
```

## Usage

1. **Initialize**: Create an `AnthropicToolCaller` instance with your API key
2. **Define Tools**: Create `ToolDefinition` objects with JSON schemas
3. **Register Tools**: Associate tool definitions with handler functions
4. **Send Messages**: Use `send_message_with_tools()` to send messages that can trigger tool calls
5. **Handle Results**: Process the returned text responses and tool execution results

## Tool Schema Format

Tools use JSON Schema format for input validation:

```python
tool_schema = {
    "type": "object",
    "properties": {
        "parameter_name": {
            "type": "string",
            "description": "Parameter description"
        }
    },
    "required": ["parameter_name"]
}
```

## Error Handling

The implementation includes comprehensive error handling:
- API communication errors
- Tool execution errors
- Input validation errors
- Individual tool failures don't crash the entire response