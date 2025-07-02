from pathlib import Path
import subprocess
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
