#!/usr/bin/env python3
"""
Create git worktrees for each approved plan in _docs/plans/approved/
Each plan gets its own feature branch and worktree directory.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    returncode, _, _ = run_command(
        ["git", "rev-parse", "--git-dir"], check=False)
    return returncode == 0


def is_working_directory_clean() -> bool:
    """Check if working directory has uncommitted changes."""
    returncode, stdout, _ = run_command(
        ["git", "status", "--porcelain"], check=False)
    return returncode == 0 and not stdout


def branch_exists(branch_name: str) -> bool:
    """Check if a branch already exists locally or remotely."""
    # Check local branches
    returncode, stdout, _ = run_command(
        ["git", "branch", "--list", branch_name], check=False)
    if stdout:
        return True

    # Check remote branches
    returncode, stdout, _ = run_command(
        ["git", "branch", "-r", "--list", f"*/{branch_name}"], check=False)
    return bool(stdout)


def create_worktree(plan_file: Path, base_dir: Path) -> bool:
    """Create a worktree for a plan file."""
    # Extract base filename without extension
    base_name = plan_file.stem

    # Convert underscores to hyphens for branch name
    feature_name = base_name.replace("_", "-")

    # Create branch and directory names
    branch_name = f"feature/{feature_name}"
    worktree_dir = base_dir / f"collect-{feature_name}"

    print(f"\nProcessing: {plan_file.name}")
    print(f"  Branch: {branch_name}")
    print(f"  Directory: {worktree_dir}")

    # Check if branch already exists
    if branch_exists(branch_name):
        print(f"  ⚠️  Branch '{branch_name}' already exists, skipping...")
        return False

    # Check if worktree directory already exists
    if worktree_dir.exists():
        print(f"  ⚠️  Directory '{worktree_dir}' already exists, skipping...")
        return False

    # Create the worktree
    cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_dir)]
    returncode, stdout, stderr = run_command(cmd, check=False)

    if returncode == 0:
        print(f"  ✅ Successfully created worktree")
        return True
    else:
        print(f"  ❌ Failed to create worktree: {stderr}")
        return False


def main():
    """Main function to create worktrees for all approved plans."""
    print("Git Worktree Creator for Approved Plans")
    print("=" * 40)

    # Check if we're in a git repository
    if not is_git_repo():
        print("❌ Error: Not in a git repository!")
        sys.exit(1)

    # Check if working directory is clean
    if not is_working_directory_clean():
        print("⚠️  Warning: Working directory has uncommitted changes.")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("Exiting...")
            sys.exit(0)

    # Find the approved plans directory
    approved_dir = Path("_docs/plans/approved")
    if not approved_dir.exists():
        print(f"❌ Error: Directory '{approved_dir}' does not exist!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)

    # Get all markdown files
    plan_files = list(approved_dir.glob("*.md"))
    if not plan_files:
        print(f"No markdown files found in {approved_dir}")
        sys.exit(0)

    print(f"\nFound {len(plan_files)} plan file(s):")
    for pf in plan_files:
        print(f"  - {pf.name}")

    # Determine parent directory for worktrees
    current_dir = Path.cwd()
    parent_dir = current_dir.parent

    print(f"\nWorktrees will be created in: {parent_dir}")
    response = input("Continue? (Y/n): ").lower()
    if response == 'n':
        print("Exiting...")
        sys.exit(0)

    # Create worktrees
    created_count = 0
    failed_count = 0
    skipped_count = 0

    for plan_file in sorted(plan_files):
        success = create_worktree(plan_file, parent_dir)
        if success:
            created_count += 1
        elif success is False:
            skipped_count += 1
        else:
            failed_count += 1

    # Summary
    print("\n" + "=" * 40)
    print("Summary:")
    print(f"  ✅ Created: {created_count}")
    print(f"  ⚠️  Skipped: {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")

    if created_count > 0:
        print("\nCreated worktrees:")
        _, stdout, _ = run_command(["git", "worktree", "list"])
        print(stdout)


if __name__ == "__main__":
    main()
