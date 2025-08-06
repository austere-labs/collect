# API Server Integration with MCP Server

## Overview
This document explains how to automatically start the FastAPI server when the MCP (Model Context Protocol) server starts, ensuring both services run together.

## Problem Statement
- **collect.py**: MCP server that provides AI tools
- **api.py**: FastAPI server for HTTP endpoints
- **Goal**: Start both servers with a single command

## Proposed Solution

### Using subprocess.Popen
The solution uses Python's `subprocess` module to launch the API server as a background process when the MCP server starts.

### Implementation Details

#### 1. Import Required Modules
```python
import subprocess  # For running API as subprocess
import atexit      # For cleanup on exit
import time        # For startup delay
```

#### 2. Modified main() Function
```python
def main():
    # Start the API server in the background
    api_process = None
    try:
        # Launch API server as subprocess
        api_process = subprocess.Popen(
            ["python", "api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for API to initialize
        time.sleep(2)
        
        # Verify successful startup
        if api_process.poll() is not None:
            # Process ended unexpectedly
            stderr = api_process.stderr.read()
            print(f"API server failed to start: {stderr}")
        else:
            print(f"API server started with PID: {api_process.pid}")
            
            # Register cleanup handler
            def cleanup_api():
                if api_process and api_process.poll() is None:
                    print("Shutting down API server...")
                    api_process.terminate()
                    try:
                        api_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        api_process.kill()
            
            atexit.register(cleanup_api)
    
    except Exception as e:
        print(f"Failed to start API server: {e}")
    
    # Continue with MCP server startup
    mcp.run(transport="stdio")
```

## How It Works

### Startup Sequence
1. **Launch API Process**: Uses `subprocess.Popen()` to start `api.py` in background
2. **Non-blocking**: Popen returns immediately, allowing MCP to continue
3. **Startup Delay**: 2-second sleep gives API time to initialize
4. **Health Check**: `poll()` verifies process is still running
5. **Error Handling**: Captures stderr if API fails to start

### Process Management
- **subprocess.Popen**: Creates child process for API server
- **stdout/stderr pipes**: Captures API output (prevents terminal clutter)
- **PID tracking**: Stores process ID for management
- **Independent processes**: Both servers run in parallel

### Cleanup Mechanism
- **atexit.register()**: Ensures cleanup runs on any exit
- **Graceful shutdown**: First tries `terminate()` (SIGTERM)
- **Forced shutdown**: Uses `kill()` if graceful fails
- **Timeout handling**: 5-second grace period for cleanup

## Benefits

1. **Single Command**: Run both servers with `uv run collect.py`
2. **Automatic Cleanup**: API stops when MCP stops
3. **Error Visibility**: Failed startup is reported
4. **Process Isolation**: Servers run independently
5. **Clean Logs**: API output is captured, not mixed with MCP

## Alternative Approaches

### 1. Threading (Not Recommended)
```python
import threading
thread = threading.Thread(target=lambda: uvicorn.run(app))
thread.daemon = True
thread.start()
```
**Issue**: FastAPI/uvicorn may conflict with MCP's event loop

### 2. Multiprocessing
```python
from multiprocessing import Process
api_process = Process(target=lambda: uvicorn.run(app))
api_process.daemon = True
api_process.start()
```
**Issue**: More complex, requires importing API app

### 3. External Process Manager
- Use systemd, supervisor, or docker-compose
- **Pros**: Production-ready, robust
- **Cons**: Additional configuration required

## Usage

Once implemented, simply run:
```bash
uv run collect.py
```

This will:
1. Start the API server on configured port (from .env)
2. Start the MCP server
3. Both services run until interrupted
4. Clean shutdown on Ctrl+C

## Port Configuration
Ensure your `.env` file has:
```
PORT=8000  # Or desired port for API
```

## Debugging

If API fails to start:
1. Check port availability: `lsof -i :8000`
2. Verify environment: `uv run python api.py` (standalone)
3. Check logs in stderr capture
4. Ensure database path exists: `data/collect.db`

## Production Considerations

For production deployment, consider:
- Using proper process managers (systemd, supervisor)
- Implementing health checks and restarts
- Separating services in containers
- Using reverse proxy (nginx) for API
- Implementing proper logging to files