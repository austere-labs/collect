# Plan: Add Claude Code SDK Processing to build_worktrees()

## Overview

Enhance the `build_worktrees()` function to automatically process plan markdown files using the Claude Code SDK after creating worktrees. This will allow for automatic implementation of approved plans in their dedicated worktree environments.

## Goals

1. **Automated Plan Execution**: Automatically run approved plans through Claude Code SDK
2. **Parallel Processing**: Execute multiple plan implementations simultaneously
3. **Isolated Environments**: Each plan runs in its own worktree directory
4. **Comprehensive Reporting**: Detailed status and output for each plan execution
5. **Error Resilience**: Graceful handling of failures in individual plan processing

## Implementation Details

### Enhanced build_worktrees() Function

```python
@mcp.tool()
async def build_worktrees(auto_process: bool = False) -> dict:
    """
    Create git worktrees for approved plans in _docs/plans/approved/.
    Optionally process plans automatically using Claude Code SDK.
    
    Args:
        auto_process: If True, automatically process plan files using Claude SDK
    
    Returns:
        Dictionary with status, summary, and optional processing results
    """
    # ... existing worktree creation logic ...
    
    if auto_process and created:
        # Process plans in parallel
        processing_results = await process_plans_in_worktrees(
            created_worktrees, plan_files, parent_dir
        )
        result["processing_results"] = processing_results
    
    return result
```

### New Helper Functions

#### Core Processing Function
```python
async def process_plans_in_worktrees(
    created_worktrees: List[str], 
    plan_files: List[Path], 
    base_dir: Path
) -> List[dict]:
    """
    Process multiple plan files in parallel using Claude Code SDK.
    
    Args:
        created_worktrees: List of successfully created worktree names
        plan_files: List of corresponding plan file paths
        base_dir: Base directory containing worktrees
    
    Returns:
        List of processing results for each plan
    """
    tasks = []
    
    for worktree_name in created_worktrees:
        # Find corresponding plan file
        plan_file = next(
            (pf for pf in plan_files if pf.stem.replace("_", "-") in worktree_name),
            None
        )
        
        if plan_file:
            worktree_dir = base_dir / f"collect-{worktree_name}"
            task = process_single_plan(plan_file, worktree_dir)
            tasks.append(task)
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error dictionaries
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "status": "failed",
                "error": f"Unexpected error: {str(result)}",
                "plan_file": created_worktrees[i] if i < len(created_worktrees) else "unknown"
            })
        else:
            processed_results.append(result)
    
    return processed_results
```

#### Individual Plan Processing
```python
async def process_single_plan(plan_file: Path, worktree_dir: Path) -> dict:
    """
    Process a single plan file using Claude Code SDK in its worktree.
    
    Args:
        plan_file: Path to the markdown plan file
        worktree_dir: Path to the worktree directory
    
    Returns:
        Dictionary with processing status, output, and metadata
    """
    try:
        # Read and prepare plan content
        plan_content = plan_file.read_text(encoding='utf-8')
        processed_content = extract_plan_prompt(plan_content)
        
        # Prepare Claude Code command
        cmd = [
            "claude", 
            "-p", processed_content,
            "--dangerously-skip-permissions"
        ]
        
        # Execute in worktree directory with timeout
        start_time = time.time()
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=worktree_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600  # 10 minute timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "plan_file": plan_file.name,
                "worktree_dir": str(worktree_dir),
                "status": "failed",
                "error": "Process timed out after 10 minutes",
                "duration": time.time() - start_time
            }
        
        duration = time.time() - start_time
        
        if process.returncode == 0:
            return {
                "plan_file": plan_file.name,
                "worktree_dir": str(worktree_dir),
                "status": "success",
                "output": stdout,
                "duration": duration,
                "exit_code": process.returncode
            }
        else:
            return {
                "plan_file": plan_file.name,
                "worktree_dir": str(worktree_dir),
                "status": "failed",
                "error": stderr or "Unknown error",
                "output": stdout,
                "duration": duration,
                "exit_code": process.returncode
            }
    
    except Exception as e:
        return {
            "plan_file": plan_file.name,
            "worktree_dir": str(worktree_dir),
            "status": "failed",
            "error": f"Exception during processing: {str(e)}"
        }
```

#### Plan Content Extraction
```python
def extract_plan_prompt(plan_content: str) -> str:
    """
    Extract the main plan content from markdown, removing metadata and headers.
    
    Args:
        plan_content: Raw markdown content of the plan file
    
    Returns:
        Cleaned plan content suitable for Claude Code SDK
    """
    lines = plan_content.split('\n')
    
    # Skip YAML frontmatter if present
    if lines and lines[0].strip() == '---':
        end_frontmatter = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_frontmatter = i + 1
                break
        if end_frontmatter:
            lines = lines[end_frontmatter:]
    
    # Join and clean up
    content = '\n'.join(lines).strip()
    
    # Add instruction prefix
    prompt = f"""Please implement the following plan in this codebase:

{content}

Follow the plan step by step and implement all the required changes. Use the available tools to read existing code, make modifications, and test the implementation."""
    
    return prompt
```

## Enhanced Return Structure

```json
{
  "status": "success",
  "summary": {
    "found": 3,
    "created": 3,
    "skipped": 0,
    "failed": 0
  },
  "details": {
    "created": ["add_feature_one.md", "fix_bug_two.md"],
    "skipped": [],
    "failed": []
  },
  "worktree_dir": "/path/to/parent",
  "worktree_list": "git worktree list output",
  "processing_results": [
    {
      "plan_file": "add_feature_one.md",
      "worktree_dir": "/path/to/collect-add-feature-one",
      "status": "success",
      "output": "Implementation completed successfully...",
      "duration": 45.2,
      "exit_code": 0
    },
    {
      "plan_file": "fix_bug_two.md", 
      "worktree_dir": "/path/to/collect-fix-bug-two",
      "status": "failed",
      "error": "Command failed with exit code 1",
      "output": "Partial output...",
      "duration": 12.1,
      "exit_code": 1
    }
  ]
}
```

## Error Handling Strategy

### Command Execution Errors
- Capture both stdout and stderr
- Include exit codes in results
- Handle timeouts gracefully
- Provide detailed error messages

### File System Errors
- Handle missing plan files
- Check worktree directory existence
- Proper encoding handling for markdown files

### Parallel Processing Errors
- Use `return_exceptions=True` in `asyncio.gather()`
- Convert exceptions to structured error responses
- Continue processing other plans if one fails

### Resource Management
- Set reasonable timeouts (10 minutes default)
- Proper process cleanup on timeout/cancellation
- Memory-efficient handling of large outputs

## Configuration Options

### Environment Variables
```bash
# Optional: Customize Claude Code executable path
CLAUDE_CODE_EXECUTABLE=claude

# Optional: Set global timeout for plan processing (seconds)
CLAUDE_PLAN_TIMEOUT=600

# Optional: Set maximum parallel processes
CLAUDE_MAX_PARALLEL=5
```

### Function Parameters
- `auto_process: bool = False` - Enable automatic plan processing
- `timeout: int = 600` - Timeout in seconds for each plan
- `max_parallel: int = 5` - Maximum concurrent plan processes

## Usage Examples

### Basic Usage with Auto-processing
```python
# Create worktrees and process plans automatically
result = await build_worktrees(auto_process=True)

# Check overall status
if result["status"] == "success":
    print(f"Created {result['summary']['created']} worktrees")
    
    # Check processing results if auto_process was enabled
    if "processing_results" in result:
        for proc_result in result["processing_results"]:
            if proc_result["status"] == "success":
                print(f"✅ {proc_result['plan_file']}: Completed in {proc_result['duration']:.1f}s")
            else:
                print(f"❌ {proc_result['plan_file']}: {proc_result['error']}")
```

### Manual Processing Later
```python
# Create worktrees first
result = await build_worktrees(auto_process=False)

# Process specific plans later
if result["status"] == "success":
    # Get created worktrees and plan files
    created = result["details"]["created"]
    plan_files = [Path(f"_docs/plans/approved/{name}") for name in created]
    
    # Process manually with custom options
    processing_results = await process_plans_in_worktrees(
        created, plan_files, Path(result["worktree_dir"])
    )
```

## Testing Strategy

### Unit Tests
```python
async def test_process_single_plan_success():
    """Test successful plan processing."""
    # Create mock plan file and worktree
    # Test with simple plan content
    # Verify successful execution and output structure

async def test_process_single_plan_timeout():
    """Test plan processing timeout handling."""
    # Create plan that would run longer than timeout
    # Verify timeout handling and cleanup

async def test_extract_plan_prompt():
    """Test plan content extraction and cleaning."""
    # Test with various markdown formats
    # Test YAML frontmatter removal
    # Test content preservation
```

### Integration Tests
```python
async def test_build_worktrees_with_auto_process():
    """Test complete workflow with auto-processing."""
    # Create test repository with plans
    # Run build_worktrees with auto_process=True
    # Verify worktrees created and plans processed

async def test_parallel_plan_processing():
    """Test multiple plans processing in parallel."""
    # Create multiple plan files
    # Verify all plans process concurrently
    # Check that failures in one don't affect others
```

## Implementation Notes

### Dependencies
- Add `asyncio` import to collect.py
- Add `time` import for duration tracking
- Ensure Claude Code CLI is available in PATH

### Performance Considerations
- Limit concurrent processes to avoid resource exhaustion
- Implement backpressure for large numbers of plans
- Consider memory usage for large plan outputs

### Security Considerations
- Using `--dangerously-skip-permissions` bypasses safety checks
- Ensure this is only used in trusted, isolated environments
- Consider adding user confirmation for auto-processing

### Monitoring and Logging
- Log start/completion of each plan processing
- Track processing durations for performance monitoring
- Consider adding progress indicators for long-running operations

## Future Enhancements

1. **Progress Streaming**: Real-time updates on processing status
2. **Selective Processing**: Allow processing specific plans only
3. **Retry Logic**: Automatic retry for transient failures
4. **Output Storage**: Save Claude outputs to files in worktrees
5. **Plan Dependencies**: Support for plan execution ordering
6. **Resource Limits**: CPU/memory constraints for plan processing
7. **Integration Testing**: Automated testing of implemented plans

## Migration Path

1. **Phase 1**: Implement core functionality with `auto_process=False` default
2. **Phase 2**: Add comprehensive testing and error handling
3. **Phase 3**: Enable auto-processing by default after validation
4. **Phase 4**: Add advanced features like progress tracking and selective processing

This plan provides a comprehensive approach to integrating Claude Code SDK processing into the worktree workflow, enabling automated implementation of approved plans while maintaining robustness and flexibility.