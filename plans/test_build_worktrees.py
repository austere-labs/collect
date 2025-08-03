import pytest
import tempfile
from pathlib import Path
import subprocess
import sys
import os
from unittest.mock import patch

# Add the parent directory to the path so we can import collect
sys.path.insert(0, str(Path(__file__).parent.parent))

from collect import build_worktrees
from plans.worktree import WorktreeStatus, is_git_repo, is_working_directory_clean


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / "test_repo"
        repo_dir.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
        
        # Set default branch to main (in case git defaults to master)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
        
        # Create initial commit
        readme = repo_dir / "README.md"
        readme.write_text("# Test Repository\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True, capture_output=True)
        
        yield repo_dir


@pytest.fixture
def approved_plans_dir(temp_git_repo):
    """Create the approved plans directory structure with test files."""
    plans_dir = temp_git_repo / "_docs" / "plans" / "approved"
    plans_dir.mkdir(parents=True)
    
    # Create test plan files
    test_plans = [
        "add_feature_one.md",
        "fix_bug_two.md", 
        "update_documentation.md"
    ]
    
    for plan_name in test_plans:
        plan_file = plans_dir / plan_name
        plan_file.write_text(f"# {plan_name}\n\nThis is a test plan for {plan_name}")
    
    # Commit the plan files to avoid uncommitted changes warning
    subprocess.run(["git", "add", "_docs"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test plans"], cwd=temp_git_repo, check=True, capture_output=True)
    
    return plans_dir


@pytest.mark.asyncio
async def test_build_worktrees_success(approved_plans_dir, temp_git_repo):
    """Test successful worktree creation."""
    # Change to the test repo directory
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Run build_worktrees
        result = await build_worktrees()
        
        # Check result structure
        assert result["status"] == "success"
        assert result["summary"]["found"] == 3
        assert result["summary"]["created"] == 3
        assert result["summary"]["skipped"] == 0
        assert result["summary"]["failed"] == 0
        
        # Check that files were created
        expected_files = ["add_feature_one.md", "fix_bug_two.md", "update_documentation.md"]
        assert set(result["details"]["created"]) == set(expected_files)
        
        # Check that worktree directories were actually created
        parent_dir = temp_git_repo.parent
        expected_dirs = [
            "collect-add-feature-one",
            "collect-fix-bug-two", 
            "collect-update-documentation"
        ]
        
        for dir_name in expected_dirs:
            worktree_dir = parent_dir / dir_name
            assert worktree_dir.exists(), f"Worktree directory {worktree_dir} should exist"
            assert (worktree_dir / "README.md").exists(), f"README.md should exist in {worktree_dir}"
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_not_git_repo(tmp_path):
    """Test error when not in a git repository."""
    # Change to a non-git directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        result = await build_worktrees()
        
        assert result["status"] == "error"
        assert result["message"] == "Not in a git repository"
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_no_approved_dir(temp_git_repo):
    """Test error when approved plans directory doesn't exist."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        result = await build_worktrees()
        
        assert result["status"] == "error"
        assert "does not exist" in result["message"]
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_no_plan_files(temp_git_repo):
    """Test when approved directory exists but has no markdown files."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create empty approved directory
        plans_dir = temp_git_repo / "_docs" / "plans" / "approved"
        plans_dir.mkdir(parents=True)
        
        result = await build_worktrees()
        
        assert result["status"] == "info"
        assert "No markdown files found" in result["message"]
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_with_uncommitted_changes(approved_plans_dir, temp_git_repo):
    """Test warning when working directory has uncommitted changes."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create uncommitted changes
        test_file = temp_git_repo / "uncommitted.txt"
        test_file.write_text("This file is not committed")
        
        result = await build_worktrees()
        
        assert result["status"] == "warning"
        assert "uncommitted changes" in result["message"]
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_skip_existing_branches(approved_plans_dir, temp_git_repo):
    """Test skipping when branches already exist."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create one of the feature branches manually
        subprocess.run(["git", "checkout", "-b", "feature/add-feature-one"], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "main"], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        
        result = await build_worktrees()
        
        assert result["status"] == "success"
        assert result["summary"]["created"] == 2  # Only 2 should be created
        assert result["summary"]["skipped"] == 1  # 1 should be skipped
        
        # Check that the correct file was skipped
        assert "add_feature_one.md" in result["details"]["skipped"]
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_skip_existing_directories(approved_plans_dir, temp_git_repo):
    """Test skipping when worktree directories already exist."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create one of the worktree directories manually
        parent_dir = temp_git_repo.parent
        existing_dir = parent_dir / "collect-add-feature-one"
        existing_dir.mkdir()
        
        result = await build_worktrees()
        
        assert result["status"] == "success"
        assert result["summary"]["created"] == 2  # Only 2 should be created
        assert result["summary"]["skipped"] == 1  # 1 should be skipped
        
        # Check that the correct file was skipped
        assert "add_feature_one.md" in result["details"]["skipped"]
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_includes_worktree_list(approved_plans_dir, temp_git_repo):
    """Test that successful creation includes worktree list."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        result = await build_worktrees()
        
        assert result["status"] == "success"
        assert "worktree_list" in result
        assert result["worktree_list"]  # Should not be empty
        
        # Should contain references to created worktrees
        worktree_list = result["worktree_list"]
        assert "collect-add-feature-one" in worktree_list
        assert "collect-fix-bug-two" in worktree_list
        assert "collect-update-documentation" in worktree_list
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_correct_branch_names(approved_plans_dir, temp_git_repo):
    """Test that branch names are created correctly (underscores to hyphens)."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        await build_worktrees()
        
        # Check that branches were created with correct names
        branch_result = subprocess.run(["git", "branch", "-a"], 
                                     cwd=temp_git_repo, capture_output=True, text=True)
        branches = branch_result.stdout
        
        assert "feature/add-feature-one" in branches
        assert "feature/fix-bug-two" in branches
        assert "feature/update-documentation" in branches
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio 
async def test_build_worktrees_error_handling():
    """Test that unexpected errors are handled gracefully."""
    # This test simulates an unexpected error by mocking the worktree module
    import unittest.mock
    
    with unittest.mock.patch('plans.worktree.is_git_repo', side_effect=Exception("Unexpected error")):
        result = await build_worktrees()
        
        assert result["status"] == "error"
        assert "Unexpected error" in result["message"]


# Integration test that doesn't require git (for basic functionality)
def test_worktree_status_enum():
    """Test that WorktreeStatus enum values are correct."""
    assert WorktreeStatus.CREATED == "created"
    assert WorktreeStatus.SKIPPED == "skipped" 
    assert WorktreeStatus.FAILED == "failed"


# Test the git utility functions separately
def test_is_git_repo_functions():
    """Test git repository detection functions."""
    # These will return False in non-git environments, which is expected
    # In a CI environment without git, these should not fail
    try:
        git_result = is_git_repo()
        clean_result = is_working_directory_clean()
        # Just ensure they return boolean values
        assert isinstance(git_result, bool)
        assert isinstance(clean_result, bool)
    except FileNotFoundError:
        # Git not available, skip this test
        pytest.skip("Git not available in test environment")


@pytest.mark.asyncio
async def test_build_worktrees_auto_process_enabled(approved_plans_dir, temp_git_repo):
    """Test build_worktrees with auto_process=True."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Mock the Claude processing to avoid actually running it
        mock_results = [
            {
                "plan_file": "add_feature_one.md",
                "worktree_dir": str(temp_git_repo.parent / "collect-add-feature-one"),
                "status": "success",
                "output": "Mock implementation completed",
                "duration": 1.5,
                "exit_code": 0
            },
            {
                "plan_file": "fix_bug_two.md",
                "worktree_dir": str(temp_git_repo.parent / "collect-fix-bug-two"),
                "status": "success",
                "output": "Mock bug fixed",
                "duration": 2.0,
                "exit_code": 0
            },
            {
                "plan_file": "update_documentation.md",
                "worktree_dir": str(temp_git_repo.parent / "collect-update-documentation"),
                "status": "failed",
                "error": "Mock error occurred",
                "output": "",
                "duration": 0.5,
                "exit_code": 1
            }
        ]
        
        with patch('plans.worktree.process_plans_in_worktrees', return_value=mock_results) as mock_process:
            result = await build_worktrees(auto_process=True)
        
        # Verify worktrees were created
        assert result["status"] == "success"
        assert result["summary"]["created"] == 3
        
        # Verify processing was called
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        assert len(call_args[0]) == 3  # created worktrees
        assert len(call_args[1]) == 3  # plan files
        # Compare resolved paths to handle symlinks
        assert call_args[2].resolve() == temp_git_repo.parent.resolve()  # base directory
        
        # Verify processing results are included
        assert "processing_results" in result
        assert len(result["processing_results"]) == 3
        
        # Check individual results
        success_count = sum(1 for r in result["processing_results"] if r["status"] == "success")
        failed_count = sum(1 for r in result["processing_results"] if r["status"] == "failed")
        assert success_count == 2
        assert failed_count == 1
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_auto_process_disabled(approved_plans_dir, temp_git_repo):
    """Test that auto_process=False doesn't trigger processing."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        with patch('plans.worktree.process_plans_in_worktrees') as mock_process:
            result = await build_worktrees(auto_process=False)
        
        # Verify worktrees were created
        assert result["status"] == "success"
        assert result["summary"]["created"] == 3
        
        # Verify processing was NOT called
        mock_process.assert_not_called()
        
        # Verify no processing results
        assert "processing_results" not in result
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_auto_process_no_worktrees_created(temp_git_repo):
    """Test auto_process when no worktrees are created."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # No approved directory means no worktrees will be created
        with patch('plans.worktree.process_plans_in_worktrees') as mock_process:
            result = await build_worktrees(auto_process=True)
        
        assert result["status"] == "error"
        assert "does not exist" in result["message"]
        
        # Processing should not be called if no worktrees were created
        mock_process.assert_not_called()
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_auto_process_error_handling(approved_plans_dir, temp_git_repo):
    """Test error handling during auto-processing."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Mock processing to raise an exception
        with patch('plans.worktree.process_plans_in_worktrees', 
                  side_effect=Exception("Processing failed")):
            result = await build_worktrees(auto_process=True)
        
        # Worktrees should still be created successfully
        assert result["status"] == "success"
        assert result["summary"]["created"] == 3
        
        # Error should be captured
        assert "processing_error" in result
        assert "Failed to process plans" in result["processing_error"]
        assert "Processing failed" in result["processing_error"]
        
        # No processing_results since it failed
        assert "processing_results" not in result
    
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_build_worktrees_auto_process_partial_creation(approved_plans_dir, temp_git_repo):
    """Test auto_process when only some worktrees are created."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create one branch manually to cause a skip
        subprocess.run(["git", "checkout", "-b", "feature/add-feature-one"], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "main"], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        
        mock_results = [
            {
                "plan_file": "fix_bug_two.md",
                "status": "success",
                "output": "Processed"
            },
            {
                "plan_file": "update_documentation.md",
                "status": "success",
                "output": "Processed"
            }
        ]
        
        with patch('plans.worktree.process_plans_in_worktrees', return_value=mock_results) as mock_process:
            result = await build_worktrees(auto_process=True)
        
        assert result["status"] == "success"
        assert result["summary"]["created"] == 2  # Only 2 created
        assert result["summary"]["skipped"] == 1  # 1 skipped
        
        # Processing should only be called for created worktrees
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        assert len(call_args[0]) == 2  # Only 2 created worktrees
    
    finally:
        os.chdir(original_cwd)


# Test the actual Claude integration (requires Claude CLI)
@pytest.mark.asyncio
@pytest.mark.skipif(
    subprocess.run(["which", "claude"], capture_output=True).returncode != 0,
    reason="Claude CLI not available"
)
async def test_build_worktrees_real_claude_integration(temp_git_repo):
    """Integration test with real Claude CLI (if available)."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_git_repo)
        
        # Create a simple test plan
        plans_dir = temp_git_repo / "_docs" / "plans" / "approved"
        plans_dir.mkdir(parents=True)
        
        test_plan = plans_dir / "test_echo.md"
        test_plan.write_text("""# Test Echo Plan

Please create a file called test.txt with the content "Hello from Claude".
Use the Write tool to create the file.
""")
        
        # Commit the plan
        subprocess.run(["git", "add", "_docs"], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Add test plan"], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        
        # Run with real Claude processing
        result = await build_worktrees(auto_process=True)
        
        assert result["status"] == "success"
        assert result["summary"]["created"] == 1
        
        if "processing_results" in result:
            # Check if Claude actually created the file
            worktree_dir = temp_git_repo.parent / "collect-test-echo"
            _ = worktree_dir / "test.txt"
            
            # This might or might not succeed depending on Claude's response
            # Just verify the structure is correct
            assert len(result["processing_results"]) == 1
            assert "status" in result["processing_results"][0]
    
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__, "-v"])