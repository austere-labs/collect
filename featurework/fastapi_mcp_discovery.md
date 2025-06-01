# FastAPI with MCP Tool Discovery Endpoint

This approach creates a FastAPI HTTP server that exposes its own MCP schema and provides both direct HTTP endpoints and MCP-compatible tool calling.

## Architecture

- Single FastAPI server with dual interfaces
- HTTP endpoints for direct API calls
- MCP tool discovery endpoint (`/mcp/tools`)
- Generic MCP tool caller endpoint (`/mcp/call/{tool_name}`)
- JavaScript client that can discover and call tools

## Python Server Implementation

```python
# discoverable_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import json

app = FastAPI(
    title="MCP Discoverable API",
    description="FastAPI server with MCP tool discovery",
    version="1.0.0"
)

# Data models
class ToolArguments(BaseModel):
    arguments: Dict[str, Any]

class CalculateRequest(BaseModel):
    expression: str

class ProcessTextRequest(BaseModel):
    text: str
    operation: str = "uppercase"

# MCP tool definitions
MCP_TOOLS = [
    {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string", 
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "process_text",
        "description": "Process text with various operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to process"
                },
                "operation": {
                    "type": "string",
                    "enum": ["uppercase", "lowercase", "reverse", "word_count"],
                    "description": "Operation to perform on the text"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "get_server_info",
        "description": "Get information about the server",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# Core business logic functions
async def calculate_expression(expression: str) -> Dict[str, Any]:
    """Safely evaluate mathematical expressions"""
    try:
        # In production, use a safe math parser instead of eval
        # For demo purposes only
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        result = eval(expression)
        return {
            "result": result,
            "expression": expression,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "expression": expression,
            "status": "error"
        }

async def process_text_operation(text: str, operation: str = "uppercase") -> Dict[str, Any]:
    """Process text with various operations"""
    try:
        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "word_count":
            result = len(text.split())
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "result": result,
            "original_text": text,
            "operation": operation,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "operation": operation,
            "status": "error"
        }

async def get_server_information() -> Dict[str, Any]:
    """Get server information"""
    return {
        "name": "MCP Discoverable API",
        "version": "1.0.0",
        "available_tools": len(MCP_TOOLS),
        "endpoints": {
            "mcp_tools": "/mcp/tools",
            "mcp_call": "/mcp/call/{tool_name}",
            "direct_calculate": "/api/calculate",
            "direct_process": "/api/process",
            "docs": "/docs"
        },
        "status": "healthy"
    }

# MCP Discovery Endpoints
@app.get("/mcp/tools")
async def list_mcp_tools():
    """Expose available tools in MCP format"""
    return {
        "tools": MCP_TOOLS,
        "server_info": {
            "name": "MCP Discoverable API",
            "version": "1.0.0"
        }
    }

@app.post("/mcp/call/{tool_name}")
async def call_mcp_tool(tool_name: str, request: ToolArguments):
    """Generic MCP tool caller"""
    arguments = request.arguments
    
    if tool_name == "calculate":
        expression = arguments.get("expression")
        if not expression:
            raise HTTPException(status_code=400, detail="Missing required argument: expression")
        return await calculate_expression(expression)
    
    elif tool_name == "process_text":
        text = arguments.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Missing required argument: text")
        operation = arguments.get("operation", "uppercase")
        return await process_text_operation(text, operation)
    
    elif tool_name == "get_server_info":
        return await get_server_information()
    
    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

# Direct HTTP API Endpoints
@app.post("/api/calculate")
async def calculate_endpoint(request: CalculateRequest):
    """Direct HTTP endpoint for calculations"""
    return await calculate_expression(request.expression)

@app.post("/api/process")
async def process_text_endpoint(request: ProcessTextRequest):
    """Direct HTTP endpoint for text processing"""
    return await process_text_operation(request.text, request.operation)

@app.get("/api/info")
async def server_info_endpoint():
    """Direct HTTP endpoint for server info"""
    return await get_server_information()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Server is running"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP Discoverable API",
        "documentation": "/docs",
        "mcp_tools": "/mcp/tools",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
```

## JavaScript Client Implementation

```javascript
// mcp_http_client.js

class HTTPMCPClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.tools = null;
    }
    
    /**
     * Discover available MCP tools from the server
     */
    async discoverTools() {
        try {
            const response = await fetch(`${this.baseUrl}/mcp/tools`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.tools = data.tools;
            return data;
        } catch (error) {
            console.error('Error discovering tools:', error);
            throw error;
        }
    }
    
    /**
     * Get information about a specific tool
     */
    getToolInfo(toolName) {
        if (!this.tools) {
            throw new Error('Tools not discovered yet. Call discoverTools() first.');
        }
        return this.tools.find(tool => tool.name === toolName);
    }
    
    /**
     * List all available tools
     */
    listTools() {
        if (!this.tools) {
            throw new Error('Tools not discovered yet. Call discoverTools() first.');
        }
        return this.tools.map(tool => ({
            name: tool.name,
            description: tool.description
        }));
    }
    
    /**
     * Call an MCP tool with arguments
     */
    async callTool(toolName, arguments = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/mcp/call/${toolName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ arguments })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error calling tool ${toolName}:`, error);
            throw error;
        }
    }
    
    /**
     * Validate arguments against tool schema
     */
    validateArguments(toolName, arguments) {
        const tool = this.getToolInfo(toolName);
        if (!tool) {
            throw new Error(`Tool ${toolName} not found`);
        }
        
        const schema = tool.inputSchema;
        const required = schema.required || [];
        
        // Check required arguments
        for (const field of required) {
            if (!(field in arguments)) {
                throw new Error(`Missing required argument: ${field}`);
            }
        }
        
        return true;
    }
    
    /**
     * Call tool with validation
     */
    async callToolSafe(toolName, arguments = {}) {
        this.validateArguments(toolName, arguments);
        return await this.callTool(toolName, arguments);
    }
}

// Usage examples
async function demonstrateUsage() {
    const client = new HTTPMCPClient();
    
    try {
        // Discover available tools
        console.log('Discovering tools...');
        const discovery = await client.discoverTools();
        console.log('Server info:', discovery.server_info);
        console.log('Available tools:', client.listTools());
        
        // Call calculator tool
        console.log('\nCalling calculator...');
        const calcResult = await client.callTool('calculate', {
            expression: '2 + 2 * 3'
        });
        console.log('Calculation result:', calcResult);
        
        // Call text processor tool
        console.log('\nProcessing text...');
        const textResult = await client.callTool('process_text', {
            text: 'Hello World',
            operation: 'reverse'
        });
        console.log('Text processing result:', textResult);
        
        // Get server info
        console.log('\nGetting server info...');
        const serverInfo = await client.callTool('get_server_info', {});
        console.log('Server info:', serverInfo);
        
    } catch (error) {
        console.error('Demo failed:', error);
    }
}

// Browser usage example
function createBrowserExample() {
    return `
    <html>
    <head>
        <title>MCP HTTP Client Demo</title>
    </head>
    <body>
        <h1>MCP HTTP Client Demo</h1>
        <div id="output"></div>
        
        <script>
            ${HTTPMCPClient.toString()}
            
            async function runDemo() {
                const client = new HTTPMCPClient();
                const output = document.getElementById('output');
                
                try {
                    await client.discoverTools();
                    output.innerHTML += '<p>Tools discovered!</p>';
                    
                    const result = await client.callTool('calculate', {
                        expression: '10 * 5'
                    });
                    output.innerHTML += '<p>Calculation: ' + JSON.stringify(result) + '</p>';
                    
                } catch (error) {
                    output.innerHTML += '<p>Error: ' + error.message + '</p>';
                }
            }
            
            runDemo();
        </script>
    </body>
    </html>
    `;
}

// Node.js usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HTTPMCPClient;
}

// If running in Node.js, demonstrate usage
if (typeof window === 'undefined') {
    demonstrateUsage();
}
```

## Usage Instructions

### 1. Start the Python Server

```bash
# Install dependencies
pip install fastapi uvicorn

# Run the server
python discoverable_api.py

# Server will be available at:
# - API docs: http://localhost:8000/docs
# - MCP tools: http://localhost:8000/mcp/tools
# - Health check: http://localhost:8000/health
```

### 2. Use the JavaScript Client

```javascript
// Node.js example
const HTTPMCPClient = require('./mcp_http_client.js');

const client = new HTTPMCPClient('http://localhost:8000');

// Discover and use tools
await client.discoverTools();
const result = await client.callTool('calculate', { expression: '2 + 2' });
console.log(result); // { result: 4, expression: '2 + 2', status: 'success' }
```

### 3. Direct HTTP API Usage

```bash
# Direct calculation
curl -X POST "http://localhost:8000/api/calculate" \
     -H "Content-Type: application/json" \
     -d '{"expression": "5 * 5"}'

# Direct text processing
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "hello", "operation": "uppercase"}'
```

### 4. MCP Tool Discovery

```bash
# Discover available tools
curl http://localhost:8000/mcp/tools

# Call a tool via MCP interface
curl -X POST "http://localhost:8000/mcp/call/calculate" \
     -H "Content-Type: application/json" \
     -d '{"arguments": {"expression": "3 + 4"}}'
```

## Key Features

1. **Dual Interface**: Both direct HTTP endpoints and MCP-compatible tool calling
2. **Self-Documenting**: MCP tools are discoverable via `/mcp/tools`
3. **Validation**: Argument validation against MCP schemas
4. **Error Handling**: Consistent error responses across both interfaces
5. **Auto Documentation**: FastAPI generates OpenAPI docs at `/docs`
6. **Type Safety**: Pydantic models for request/response validation

## Extension Points

- Add authentication/authorization
- Implement rate limiting
- Add more complex tools
- Integrate with databases
- Add WebSocket support for real-time tools
- Create tool composition/chaining capabilities