from pathlib import Path
import subprocess
import asyncio
import time
from typing import List, Tuple, Optional, Union
from enum import Enum
from pydantic import BaseModel


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
    returncode, stdout, _ = run_command(
        ["git", "worktree", "list", "--porcelain"], check=False)
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


async def commit_worktree_changes(worktree_path: Path, commit_message: str) -> dict:
    """
    Commit all changes in a worktree.

    Args:
        worktree_path: Path to the worktree directory
        commit_message: Git commit message

    Returns:
        Dictionary with commit status and details
    """
    try:
        # Check if path exists and is a directory
        if not worktree_path.exists() or not worktree_path.is_dir():
            return {
                "status": "failed",
                "error": f"Worktree path does not exist: {worktree_path}"
            }

        # Check git status
        returncode, status_output, _ = run_command(
            ["git", "status", "--porcelain"], check=False
        )

        if returncode != 0:
            return {
                "status": "failed",
                "error": "Failed to get git status"
            }

        if not status_output:
            return {
                "status": "no_changes",
                "message": "No changes to commit"
            }

        # Add all changes
        returncode, _, stderr = run_command(
            ["git", "add", "."], check=False
        )

        if returncode != 0:
            return {
                "status": "failed",
                "error": f"Failed to add changes: {stderr}"
            }

        # Commit changes
        returncode, stdout, stderr = run_command(
            ["git", "commit", "-m", commit_message], check=False
        )

        if returncode != 0:
            return {
                "status": "failed",
                "error": f"Failed to commit: {stderr}"
            }

        # Get commit SHA
        returncode, commit_sha, _ = run_command(
            ["git", "rev-parse", "HEAD"], check=False
        )

        return {
            "status": "success",
            "commit_sha": commit_sha,
            "commit_output": stdout,
            "files_changed": len(status_output.strip().split('\n')) if status_output else 0
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"Exception during commit: {str(e)}"
        }


async def push_feature_branch(worktree_path: Path) -> dict:
    """
    Push the current branch to remote with upstream tracking.

    Args:
        worktree_path: Path to the worktree directory

    Returns:
        Dictionary with push status and details
    """
    try:
        # Get current branch name
        returncode, branch_name, stderr = run_command(
            ["git", "branch", "--show-current"], check=False
        )

        if returncode != 0:
            return {
                "status": "failed",
                "error": f"Failed to get branch name: {stderr}"
            }

        if not branch_name:
            return {
                "status": "failed",
                "error": "No current branch found"
            }

        # Push with upstream tracking
        returncode, stdout, stderr = run_command(
            ["git", "push", "-u", "origin", branch_name], check=False
        )

        if returncode != 0:
            return {
                "status": "failed",
                "error": f"Failed to push branch: {stderr}",
                "branch_name": branch_name
            }

        return {
            "status": "success",
            "branch_name": branch_name,
            "push_output": stdout
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"Exception during push: {str(e)}"
        }


async def create_pull_request(worktree_path: Path, pr_title: str, pr_body: str = "") -> dict:
    """
    Create a pull request using GitHub CLI.

    Args:
        worktree_path: Path to the worktree directory
        pr_title: Pull request title
        pr_body: Pull request description

    Returns:
        Dictionary with PR creation status and details
    """
    try:
        # Check if gh CLI is available
        returncode, _, _ = run_command(["which", "gh"], check=False)
        if returncode != 0:
            return {
                "status": "failed",
                "error": """
                GitHub CLI (gh) is not available. install with cmd:
                brew install gh
                """
            }

        # Prepare command
        cmd = ["gh", "pr", "create", "--title", pr_title]

        if pr_body:
            cmd.extend(["--body", pr_body])
        else:
            # Use default body
            cmd.extend(
                ["--body", f"""
                Automated implementation from worktree: {worktree_path.name}
                """])

        # Create PR
        returncode, stdout, stderr = run_command(cmd, check=False)

        if returncode != 0:
            return {
                "status": "failed",
                "error": f"Failed to create PR: {stderr}"
            }

        # Extract PR URL from output
        pr_url = stdout.strip()

        # Try to extract PR number from URL
        pr_number = None
        if pr_url and "/pull/" in pr_url:
            try:
                pr_number = int(pr_url.split("/pull/")[-1])
            except (ValueError, IndexError):
                pass

        return {
            "status": "success",
            "pr_url": pr_url,
            "pr_number": pr_number,
            "pr_title": pr_title
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"Exception during PR creation: {str(e)}"
        }


async def cleanup_worktree_after_pr(worktree_path: Path) -> dict:
    """
    Clean up worktree after successful PR creation.

    Args:
        worktree_path: Path to the worktree directory

    Returns:
        Dictionary with cleanup status and details
    """
    try:
        actions_taken = []

        # Get branch name before removing worktree
        returncode, branch_name, _ = run_command(
            ["git", "branch", "--show-current"], check=False
        )

        # Remove the worktree
        result = remove_worktree(worktree_path)
        if result.status == WorktreeStatus.CREATED:  # Using CREATED for success
            actions_taken.append(f"Removed worktree: {worktree_path}")
        else:
            return {
                "status": "failed",
                "error": f"Failed to remove worktree: {result.message}"
            }

        return {
            "status": "success",
            "actions_taken": actions_taken,
            "removed_path": str(worktree_path),
            "branch_name": branch_name if returncode == 0 else "unknown"
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"Exception during cleanup: {str(e)}"
        }


def validate_worktree_path(worktree_path: str) -> tuple[bool, str, Path]:
    """
    Validate and normalize worktree path.

    Args:
        worktree_path: String path to worktree

    Returns:
        Tuple of(is_valid, error_message, normalized_path)
    """
    try:
        path = Path(worktree_path).resolve()

        if not path.exists():
            return False, f"Path does not exist: {path}", path

        if not path.is_dir():
            return False, f"Path is not a directory: {path}", path

        # Check if it's a git worktree by looking for .git file or directory
        git_path = path / ".git"
        if not git_path.exists():
            return False, f"Not a git worktree (no .git found): {path}", path

        # Check if it's a worktree by checking for .git file
        # (worktrees have .git files, not dirs)
        if git_path.is_file():
            # This is likely a worktree
            return True, "", path
        elif git_path.is_dir():
            # This might be the main repository
            return True, "", path
        else:
            return False, f"Invalid git directory structure: {path}", path

    except Exception as e:
        return False, f"Error validating path: {str(e)}", Path(worktree_path)


async def finalize_worktree(
    worktree_path: str,
    commit_message: str = "Implement plan from worktree",
    pr_title: str = "",
    pr_body: str = "",
    cleanup: bool = True
) -> dict:
    """
    Finalize a worktree by committing changes, pushing to remote, creating a PR, and optionally cleaning up.
    
    Args:
        worktree_path: Path to the worktree directory
        commit_message: Git commit message (default: "Implement plan from worktree")
        pr_title: Pull request title (auto-generated if empty)
        pr_body: Pull request description (auto-generated if empty)
        cleanup: Whether to remove the worktree after successful PR creation
    
    Returns:
        Dictionary with status and details of all operations
    """
    try:
        # Validate worktree path
        is_valid, error_msg, normalized_path = validate_worktree_path(worktree_path)
        if not is_valid:
            return {
                "status": "failed",
                "error": f"Invalid worktree path: {error_msg}"
            }
        
        result = {
            "status": "success",
            "worktree_path": str(normalized_path),
            "operations": []
        }
        
        # Step 1: Commit changes
        commit_result = await commit_worktree_changes(normalized_path, commit_message)
        result["operations"].append({"step": "commit", "result": commit_result})
        
        if commit_result["status"] == "no_changes":
            result["message"] = "No changes to commit in worktree"
            return result
        elif commit_result["status"] != "success":
            result["status"] = "failed"
            result["error"] = f"Failed to commit changes: {commit_result.get('error', 'Unknown error')}"
            return result
        
        # Step 2: Push to remote
        push_result = await push_feature_branch(normalized_path)
        result["operations"].append({"step": "push", "result": push_result})
        
        if push_result["status"] != "success":
            result["status"] = "failed"
            result["error"] = f"Failed to push branch: {push_result.get('error', 'Unknown error')}"
            return result
        
        branch_name = push_result["branch_name"]
        
        # Step 3: Create PR
        if not pr_title:
            pr_title = f"Implement plan from {normalized_path.name}"
        
        if not pr_body:
            pr_body = f"""Automated implementation from worktree: {normalized_path.name}

Branch: {branch_name}
Commit: {commit_result.get('commit_sha', 'unknown')}
Files changed: {commit_result.get('files_changed', 'unknown')}

🤖 Generated with Claude Code"""
        
        pr_result = await create_pull_request(normalized_path, pr_title, pr_body)
        result["operations"].append({"step": "create_pr", "result": pr_result})
        
        if pr_result["status"] != "success":
            result["status"] = "failed"
            result["error"] = f"Failed to create PR: {pr_result.get('error', 'Unknown error')}"
            return result
        
        result["pr_url"] = pr_result["pr_url"]
        result["pr_number"] = pr_result.get("pr_number")
        
        # Step 4: Optional cleanup
        if cleanup:
            cleanup_result = await cleanup_worktree_after_pr(normalized_path)
            result["operations"].append({"step": "cleanup", "result": cleanup_result})
            
            if cleanup_result["status"] != "success":
                # Don't fail the whole operation if cleanup fails
                result["cleanup_warning"] = f"Cleanup failed: {cleanup_result.get('error', 'Unknown error')}"
            else:
                result["cleanup_success"] = True
        
        result["summary"] = {
            "branch_name": branch_name,
            "commit_sha": commit_result.get("commit_sha", "unknown"),
            "files_changed": commit_result.get("files_changed", 0),
            "pr_url": pr_result["pr_url"],
            "pr_number": pr_result.get("pr_number"),
            "cleanup_performed": cleanup
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Unexpected error during finalization: {str(e)}"
        }
