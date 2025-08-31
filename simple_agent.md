# Simple Agent System

## Overview
Build a basic AI agent that can use tools to solve tasks. The agent plans, executes, and validates its actions using an LLM for reasoning.

## Core Components

```
┌─────────────────────────────────┐
│           Agent                 │
├─────────────────────────────────┤
│  LLM Client │ Tool Registry     │
│  Planner    │ Executor          │
│  Memory     │ Error Handler     │
└─────────────────────────────────┘
```

## Implementation

### 1. Basic Data Models

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

class ExecutionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"

@dataclass
class ExecutionStep:
    tool: str
    parameters: Dict[str, Any]
    result: Optional[Any]
    status: ExecutionStatus
    error: Optional[str]

@dataclass
class AgentContext:
    user_prompt: str
    plan: List[Dict[str, Any]]
    execution_history: List[ExecutionStep]
    memory: Dict[str, Any]
```

### 2. Tool System

```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
```

### 3. LLM Client

```python
class LLMClient:
    async def generate_plan(self, prompt: str, tools: List[str]) -> List[Dict]:
        """Generate execution plan using LLM"""
        planning_prompt = f"""
        Create a step-by-step plan for: {prompt}
        
        Available tools: {', '.join(tools)}
        
        Return JSON array: [{"step": 1, "tool": "tool_name", "parameters": {...}}]
        """
        # Call LLM API and return parsed plan
        pass
        
    async def extract_parameters(self, step: Dict, context: Dict) -> Dict:
        """Extract parameters for tool execution"""
        # Use LLM to determine parameters from context
        pass
```

### 4. Main Agent

```python
class SimpleAgent:
    def __init__(self, llm_client: LLMClient, tool_registry: ToolRegistry):
        self.llm = llm_client
        self.tools = tool_registry
        
    async def run(self, prompt: str) -> Dict[str, Any]:
        # Create context
        context = AgentContext(
            user_prompt=prompt,
            plan=[],
            execution_history=[],
            memory={}
        )
        
        # Generate plan
        tool_names = list(self.tools._tools.keys())
        context.plan = await self.llm.generate_plan(prompt, tool_names)
        
        # Execute plan
        for step_data in context.plan:
            result = await self._execute_step(step_data, context)
            context.execution_history.append(result)
            
            if result.status == ExecutionStatus.FAILURE:
                return {"success": False, "error": result.error}
                
            # Store result in memory
            context.memory[f"step_{step_data['step']}"] = result.result
            
        return {"success": True, "result": context.execution_history[-1].result}
        
    async def _execute_step(self, step_data: Dict, context: AgentContext) -> ExecutionStep:
        tool = self.tools.get(step_data["tool"])
        if not tool:
            return ExecutionStep(
                tool=step_data["tool"],
                parameters={},
                result=None,
                status=ExecutionStatus.FAILURE,
                error=f"Tool {step_data['tool']} not found"
            )
            
        # Get parameters
        if "parameters" in step_data:
            params = step_data["parameters"]
        else:
            params = await self.llm.extract_parameters(step_data, context.memory)
            
        # Execute tool
        try:
            result = await tool.execute(**params)
            return ExecutionStep(
                tool=step_data["tool"],
                parameters=params,
                result=result,
                status=ExecutionStatus.SUCCESS,
                error=None
            )
        except Exception as e:
            return ExecutionStep(
                tool=step_data["tool"],
                parameters=params,
                result=None,
                status=ExecutionStatus.FAILURE,
                error=str(e)
            )
```

## Example Tools

### Calculator Tool
```python
class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__("calculator", "Perform math calculations")
        
    async def execute(self, expression: str) -> Dict[str, Any]:
        try:
            result = eval(expression)  # Note: Use safe_eval in production
            return {"result": result}
        except Exception as e:
            raise Exception(f"Calculation error: {e}")
```

### Web Search Tool
```python
class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__("web_search", "Search the web")
        
    async def execute(self, query: str) -> Dict[str, Any]:
        # Implement actual web search
        return {"results": [{"title": "...", "url": "...", "snippet": "..."}]}
```

## Usage Example

```python
# Setup
llm = LLMClient(api_key="your-key")
registry = ToolRegistry()
registry.register(CalculatorTool())
registry.register(WebSearchTool())

agent = SimpleAgent(llm, registry)

# Run
result = await agent.run("Calculate 15% tip on a $47.50 bill")
print(result)  # {"success": True, "result": 7.125}
```

## Key Features

1. **Simple Planning**: LLM generates step-by-step execution plan
2. **Tool Execution**: Execute tools with parameters from context
3. **Memory**: Store results between steps for context
4. **Error Handling**: Basic failure detection and reporting
5. **Extensible**: Easy to add new tools

## Next Steps

1. Add retry logic for failed steps
2. Implement validation of results  
3. Add logging and metrics
4. Create more sophisticated planning
5. Add parallel execution for independent steps

This simplified version focuses on the core agent loop: Plan → Execute → Store Results → Repeat.
