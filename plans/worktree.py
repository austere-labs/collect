from pathlib import Path
import subprocess
import asyncio
import time
from typing import List, Tuple, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


class WorktreeStatus(str, Enum):
    """Status of worktree creation operation"""
    CREATED = "created"
    SKIPPED = "skipped"
    FAILED = "failed"


class WorktreeResult(BaseModel):
    """Result of worktree creation attempt"""
    status: WorktreeStatus
    message: str
    branch_name: Optional[str] = None
    worktree_dir: Optional[Path] = None
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {Path: str}
    }


class WorktreeInfo(BaseModel):
    """Information about an existing worktree"""
    path: Path
    branch: Optional[str] = None
    head: Optional[str] = None
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {Path: str}
    }


def create(plan_file: Path, base_dir: Path) -> WorktreeResult:
    """
    Create a worktree for a plan file.
    
    Args:
        plan_file: Path to the plan markdown file
        base_dir: Base directory where worktrees will be created
        
    Returns:
        WorktreeResult with status and details
    """
    # Extract base file name minus extension
    base_name = plan_file.stem
    
    # Replace underscores with hyphens for branch naming
    feature_name = base_name.replace("_", "-")
    
    # Create branch and directory names
    branch_name = f"feature/{feature_name}"
    worktree_dir = base_dir / f"collect-{feature_name}"
    
    # Check if branch already exists
    if branch_exists(branch_name):
        return WorktreeResult(
            status=WorktreeStatus.SKIPPED,
            message=f"Branch '{branch_name}' already exists",
            branch_name=branch_name,
            worktree_dir=worktree_dir
        )
    
    # Check if worktree directory already exists
    if worktree_dir.exists():
        return WorktreeResult(
            status=WorktreeStatus.SKIPPED,
            message=f"Directory '{worktree_dir}' already exists",
            branch_name=branch_name,
            worktree_dir=worktree_dir
        )
    
    # Create the worktree
    cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_dir)]
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode == 0:
        return WorktreeResult(
            status=WorktreeStatus.CREATED,
            message="Successfully created worktree",
            branch_name=branch_name,
            worktree_dir=worktree_dir
        )
    else:
        return WorktreeResult(
            status=WorktreeStatus.FAILED,
            message=f"Failed to create worktree: {stderr}",
            branch_name=branch_name,
            worktree_dir=worktree_dir
        )


def create_batch(plan_files: List[Path], base_dir: Path) -> List[WorktreeResult]:
    """
    Create worktrees for multiple plan files.
    
    Args:
        plan_files: List of plan markdown files
        base_dir: Base directory where worktrees will be created
        
    Returns:
        List of WorktreeResult objects
    """
    results = []
    for plan_file in sorted(plan_files):
        result = create(plan_file, base_dir)
        results.append(result)
    return results


def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, and stderr.
    
    Args:
        cmd: Command and arguments to run
        check: Whether to print error on non-zero exit code
        
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        # Consider logging instead of printing in production
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def branch_exists(branch_name: str) -> bool:
    """
    Check if a branch already exists locally or remotely.
    
    Args:
        branch_name: Name of the branch to check
        
    Returns:
        True if branch exists, False otherwise
    """
    # Check local branches for the exact branch name
    returncode, stdout, _ = run_command(
        ["git", "branch", "--list", branch_name], check=False)
    if stdout:
        return True
    
    # Check remote branches for the branch name
    returncode, stdout, _ = run_command(
        ["git", "branch", "-r", "--list", f"*/{branch_name}"], check=False)
    return bool(stdout)


def is_git_repo() -> bool:
    """
    Check if current directory is a git repository.
    
    Returns:
        True if in a git repository, False otherwise
    """
    returncode, _, _ = run_command(
        ["git", "rev-parse", "--git-dir"], check=False)
    return returncode == 0


def is_working_directory_clean() -> bool:
    """
    Check if working directory has uncommitted changes.
    
    Returns:
        True if working directory is clean, False otherwise
    """
    returncode, stdout, _ = run_command(
        ["git", "status", "--porcelain"], check=False)
    return returncode == 0 and not stdout


def list_worktrees() -> List[WorktreeInfo]:
    """
    List all git worktrees.
    
    Returns:
        List of WorktreeInfo objects
    """
    returncode, stdout, _ = run_command(["git", "worktree", "list", "--porcelain"], check=False)
    if returncode != 0:
        return []
    
    worktrees = []
    current = {}
    
    for line in stdout.split('\n'):
        if not line:
            if current:
                worktrees.append(WorktreeInfo(**current))
                current = {}
        elif line.startswith('worktree '):
            current['path'] = Path(line[9:])
        elif line.startswith('branch '):
            current['branch'] = line[7:]
        elif line.startswith('HEAD '):
            current['head'] = line[5:]
    
    if current:
        worktrees.append(WorktreeInfo(**current))
    
    return worktrees


def remove_worktree(path: Union[str, Path], force: bool = False) -> WorktreeResult:
    """
    Remove a git worktree.
    
    Args:
        path: Path to the worktree to remove
        force: Force removal even if there are uncommitted changes
        
    Returns:
        WorktreeResult with status and details
    """
    cmd = ["git", "worktree", "remove", str(path)]
    if force:
        cmd.append("--force")
    
    returncode, stdout, stderr = run_command(cmd, check=False)
    if returncode == 0:
        return WorktreeResult(
            status=WorktreeStatus.CREATED,  # Could add REMOVED status
            message="Worktree removed successfully",
            worktree_dir=Path(path)
        )
    else:
        return WorktreeResult(
            status=WorktreeStatus.FAILED,
            message=f"Failed to remove worktree: {stderr}",
            worktree_dir=Path(path)
        )


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
