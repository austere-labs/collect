import pytest
import asyncio
import tempfile
import subprocess
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plans.worktree import (
    finalize_worktree,
    validate_worktree_path,
    commit_worktree_changes,
    push_feature_branch,
    create_pull_request,
    cleanup_worktree_after_pr,
    WorktreeStatus,
    WorktreeResult
)


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
        
        # Set default branch to main
        subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
        
        # Create initial commit
        readme = repo_dir / "README.md"
        readme.write_text("# Test Repository\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True, capture_output=True)
        
        yield repo_dir


@pytest.fixture
def temp_worktree(temp_git_repo):
    """Create a temporary git worktree for testing."""
    parent_dir = temp_git_repo.parent
    worktree_dir = parent_dir / "test-worktree"
    
    # Create worktree with feature branch
    subprocess.run([
        "git", "worktree", "add", "-b", "feature/test-branch", str(worktree_dir)
    ], cwd=temp_git_repo, check=True, capture_output=True)
    
    # Add some test content
    test_file = worktree_dir / "test.txt"
    test_file.write_text("Test content for worktree")
    
    yield worktree_dir
    
    # Cleanup worktree if it still exists
    if worktree_dir.exists():
        try:
            subprocess.run(["git", "worktree", "remove", str(worktree_dir), "--force"], 
                         cwd=temp_git_repo, check=False, capture_output=True)
        except:
            pass


class TestValidateWorktreePath:
    """Test worktree path validation."""
    
    def test_valid_worktree_path(self, temp_worktree):
        """Test validation of a valid worktree path."""
        is_valid, error_msg, normalized_path = validate_worktree_path(str(temp_worktree))
        
        assert is_valid is True
        assert error_msg == ""
        assert normalized_path == temp_worktree.resolve()
    
    def test_nonexistent_path(self):
        """Test validation of non-existent path."""
        is_valid, error_msg, _ = validate_worktree_path("/nonexistent/path")
        
        assert is_valid is False
        assert "Path does not exist" in error_msg
    
    def test_path_is_file(self, temp_git_repo):
        """Test validation when path is a file, not directory."""
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("test")
        
        is_valid, error_msg, _ = validate_worktree_path(str(test_file))
        
        assert is_valid is False
        assert "Path is not a directory" in error_msg
    
    def test_not_git_repo(self, tmp_path):
        """Test validation when path is not a git repository."""
        test_dir = tmp_path / "not_git"
        test_dir.mkdir()
        
        is_valid, error_msg, _ = validate_worktree_path(str(test_dir))
        
        assert is_valid is False
        assert "Not a git worktree" in error_msg


class TestCommitWorktreeChanges:
    """Test committing changes in worktree."""
    
    @pytest.mark.asyncio
    async def test_commit_with_changes(self, temp_worktree):
        """Test committing when there are changes."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_worktree)
            
            result = await commit_worktree_changes(temp_worktree, "Test commit message")
            
            assert result["status"] == "success"
            assert "commit_sha" in result
            assert result["files_changed"] > 0
            assert "test.txt" in subprocess.run(
                ["git", "ls-files"], cwd=temp_worktree, capture_output=True, text=True
            ).stdout
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_commit_no_changes(self, temp_worktree):
        """Test committing when there are no changes."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_worktree)
            
            # First commit the test file
            subprocess.run(["git", "add", "."], cwd=temp_worktree, check=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=temp_worktree, check=True)
            
            # Now try to commit again with no changes
            result = await commit_worktree_changes(temp_worktree, "No changes")
            
            assert result["status"] == "no_changes"
            assert result["message"] == "No changes to commit"
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_commit_invalid_path(self):
        """Test committing with invalid worktree path."""
        result = await commit_worktree_changes(Path("/nonexistent"), "Test")
        
        assert result["status"] == "failed"
        assert "does not exist" in result["error"]


class TestPushFeatureBranch:
    """Test pushing feature branch to remote."""
    
    @pytest.mark.asyncio
    async def test_push_with_mocked_git(self, temp_worktree):
        """Test push operation with mocked git commands."""
        with patch('plans.worktree.run_command') as mock_run:
            # Mock successful branch name retrieval
            mock_run.side_effect = [
                (0, "feature/test-branch", ""),  # git branch --show-current
                (0, "Pushed successfully", "")   # git push -u origin branch
            ]
            
            result = await push_feature_branch(temp_worktree)
            
            assert result["status"] == "success"
            assert result["branch_name"] == "feature/test-branch"
            assert "push_output" in result
            
            # Verify git commands were called
            assert mock_run.call_count == 2
            mock_run.assert_any_call(["git", "branch", "--show-current"], check=False)
            mock_run.assert_any_call(["git", "push", "-u", "origin", "feature/test-branch"], check=False)
    
    @pytest.mark.asyncio
    async def test_push_no_branch(self, temp_worktree):
        """Test push when no current branch is found."""
        with patch('plans.worktree.run_command') as mock_run:
            mock_run.return_value = (0, "", "")  # Empty branch name
            
            result = await push_feature_branch(temp_worktree)
            
            assert result["status"] == "failed"
            assert "No current branch found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_push_failure(self, temp_worktree):
        """Test push operation failure."""
        with patch('plans.worktree.run_command') as mock_run:
            mock_run.side_effect = [
                (0, "feature/test-branch", ""),     # git branch --show-current
                (1, "", "Permission denied")        # git push failure
            ]
            
            result = await push_feature_branch(temp_worktree)
            
            assert result["status"] == "failed"
            assert "Failed to push branch" in result["error"]
            assert "Permission denied" in result["error"]


class TestCreatePullRequest:
    """Test pull request creation."""
    
    @pytest.mark.asyncio
    async def test_create_pr_success(self, temp_worktree):
        """Test successful PR creation."""
        with patch('plans.worktree.run_command') as mock_run:
            # Mock gh CLI availability and successful PR creation
            mock_run.side_effect = [
                (0, "/usr/bin/gh", ""),  # which gh
                (0, "https://github.com/user/repo/pull/123", "")  # gh pr create
            ]
            
            result = await create_pull_request(
                temp_worktree, 
                "Test PR Title", 
                "Test PR body content"
            )
            
            assert result["status"] == "success"
            assert result["pr_url"] == "https://github.com/user/repo/pull/123"
            assert result["pr_number"] == 123
            assert result["pr_title"] == "Test PR Title"
            
            # Verify gh command was called correctly
            pr_call = mock_run.call_args_list[1]
            assert pr_call[0][0][:4] == ["gh", "pr", "create", "--title"]
            assert "Test PR Title" in pr_call[0][0]
            assert "--body" in pr_call[0][0]
    
    @pytest.mark.asyncio
    async def test_create_pr_no_gh_cli(self, temp_worktree):
        """Test PR creation when GitHub CLI is not available."""
        with patch('plans.worktree.run_command') as mock_run:
            mock_run.return_value = (1, "", "")  # which gh fails
            
            result = await create_pull_request(temp_worktree, "Test PR", "")
            
            assert result["status"] == "failed"
            assert "GitHub CLI (gh) is not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_pr_with_default_body(self, temp_worktree):
        """Test PR creation with auto-generated body."""
        with patch('plans.worktree.run_command') as mock_run:
            mock_run.side_effect = [
                (0, "/usr/bin/gh", ""),
                (0, "https://github.com/user/repo/pull/456", "")
            ]
            
            result = await create_pull_request(temp_worktree, "Test PR", "")
            
            assert result["status"] == "success"
            # Verify default body was used
            pr_call = mock_run.call_args_list[1]
            body_index = pr_call[0][0].index("--body") + 1
            assert temp_worktree.name in pr_call[0][0][body_index]


class TestCleanupWorktreeAfterPr:
    """Test worktree cleanup after PR creation."""
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, temp_worktree):
        """Test successful worktree cleanup."""
        with patch('plans.worktree.run_command') as mock_run, \
             patch('plans.worktree.remove_worktree') as mock_remove:
            
            mock_run.return_value = (0, "feature/test-branch", "")
            mock_remove.return_value = WorktreeResult(
                status=WorktreeStatus.CREATED,  # Using CREATED for success
                message="Worktree removed successfully",
                worktree_dir=temp_worktree
            )
            
            result = await cleanup_worktree_after_pr(temp_worktree)
            
            assert result["status"] == "success"
            assert f"Removed worktree: {temp_worktree}" in result["actions_taken"]
            assert result["branch_name"] == "feature/test-branch"
            assert result["removed_path"] == str(temp_worktree)
    
    @pytest.mark.asyncio
    async def test_cleanup_failure(self, temp_worktree):
        """Test worktree cleanup failure."""
        with patch('plans.worktree.run_command') as mock_run, \
             patch('plans.worktree.remove_worktree') as mock_remove:
            
            mock_run.return_value = (0, "feature/test-branch", "")
            mock_remove.return_value = WorktreeResult(
                status=WorktreeStatus.FAILED,
                message="Failed to remove worktree",
                worktree_dir=temp_worktree
            )
            
            result = await cleanup_worktree_after_pr(temp_worktree)
            
            assert result["status"] == "failed"
            assert "Failed to remove worktree" in result["error"]


class TestFinalizeWorktreeEndToEnd:
    """Test the complete finalize_worktree workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_success(self, temp_worktree):
        """Test successful end-to-end finalization workflow."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push, \
             patch('plans.worktree.create_pull_request') as mock_pr, \
             patch('plans.worktree.cleanup_worktree_after_pr') as mock_cleanup:
            
            # Mock successful operations
            mock_commit.return_value = {
                "status": "success",
                "commit_sha": "abc123",
                "files_changed": 2
            }
            
            mock_push.return_value = {
                "status": "success",
                "branch_name": "feature/test-branch"
            }
            
            mock_pr.return_value = {
                "status": "success",
                "pr_url": "https://github.com/user/repo/pull/789",
                "pr_number": 789
            }
            
            mock_cleanup.return_value = {
                "status": "success",
                "actions_taken": ["Removed worktree"]
            }
            
            result = await finalize_worktree(
                str(temp_worktree),
                commit_message="Custom commit message",
                pr_title="Custom PR Title",
                pr_body="Custom PR body",
                cleanup=True
            )
            
            # Verify overall success
            assert result["status"] == "success"
            assert result["pr_url"] == "https://github.com/user/repo/pull/789"
            assert result["pr_number"] == 789
            
            # Verify all operations were called (using .resolve() to handle symlinks)
            mock_commit.assert_called_once_with(temp_worktree.resolve(), "Custom commit message")
            mock_push.assert_called_once_with(temp_worktree.resolve())
            mock_pr.assert_called_once_with(temp_worktree.resolve(), "Custom PR Title", "Custom PR body")
            mock_cleanup.assert_called_once_with(temp_worktree.resolve())
            
            # Verify operations tracking
            assert len(result["operations"]) == 4
            operation_steps = [op["step"] for op in result["operations"]]
            assert operation_steps == ["commit", "push", "create_pr", "cleanup"]
            
            # Verify summary
            summary = result["summary"]
            assert summary["branch_name"] == "feature/test-branch"
            assert summary["commit_sha"] == "abc123"
            assert summary["files_changed"] == 2
            assert summary["cleanup_performed"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_no_changes_to_commit(self, temp_worktree):
        """Test workflow when there are no changes to commit."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit:
            mock_commit.return_value = {
                "status": "no_changes",
                "message": "No changes to commit"
            }
            
            result = await finalize_worktree(str(temp_worktree))
            
            assert result["status"] == "success"
            assert result["message"] == "No changes to commit in worktree"
            assert len(result["operations"]) == 1  # Only commit operation
    
    @pytest.mark.asyncio
    async def test_workflow_commit_failure(self, temp_worktree):
        """Test workflow when commit operation fails."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit:
            mock_commit.return_value = {
                "status": "failed",
                "error": "Commit failed"
            }
            
            result = await finalize_worktree(str(temp_worktree))
            
            assert result["status"] == "failed"
            assert "Failed to commit changes" in result["error"]
            assert "Commit failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_push_failure(self, temp_worktree):
        """Test workflow when push operation fails."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push:
            
            mock_commit.return_value = {"status": "success", "commit_sha": "abc123"}
            mock_push.return_value = {"status": "failed", "error": "Push failed"}
            
            result = await finalize_worktree(str(temp_worktree))
            
            assert result["status"] == "failed"
            assert "Failed to push branch" in result["error"]
            assert "Push failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_pr_failure(self, temp_worktree):
        """Test workflow when PR creation fails."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push, \
             patch('plans.worktree.create_pull_request') as mock_pr:
            
            mock_commit.return_value = {"status": "success", "commit_sha": "abc123"}
            mock_push.return_value = {"status": "success", "branch_name": "feature/test"}
            mock_pr.return_value = {"status": "failed", "error": "PR creation failed"}
            
            result = await finalize_worktree(str(temp_worktree))
            
            assert result["status"] == "failed"
            assert "Failed to create PR" in result["error"]
            assert "PR creation failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_cleanup_disabled(self, temp_worktree):
        """Test workflow with cleanup disabled."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push, \
             patch('plans.worktree.create_pull_request') as mock_pr, \
             patch('plans.worktree.cleanup_worktree_after_pr') as mock_cleanup:
            
            mock_commit.return_value = {"status": "success", "commit_sha": "abc123"}
            mock_push.return_value = {"status": "success", "branch_name": "feature/test"}
            mock_pr.return_value = {"status": "success", "pr_url": "https://github.com/user/repo/pull/456"}
            
            result = await finalize_worktree(str(temp_worktree), cleanup=False)
            
            assert result["status"] == "success"
            assert len(result["operations"]) == 3  # No cleanup operation
            assert result["summary"]["cleanup_performed"] is False
            mock_cleanup.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_cleanup_failure_graceful(self, temp_worktree):
        """Test workflow when cleanup fails but doesn't fail the whole operation."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push, \
             patch('plans.worktree.create_pull_request') as mock_pr, \
             patch('plans.worktree.cleanup_worktree_after_pr') as mock_cleanup:
            
            mock_commit.return_value = {"status": "success", "commit_sha": "abc123"}
            mock_push.return_value = {"status": "success", "branch_name": "feature/test"}
            mock_pr.return_value = {"status": "success", "pr_url": "https://github.com/user/repo/pull/456"}
            mock_cleanup.return_value = {"status": "failed", "error": "Cleanup failed"}
            
            result = await finalize_worktree(str(temp_worktree), cleanup=True)
            
            assert result["status"] == "success"  # Still success despite cleanup failure
            assert "cleanup_warning" in result
            assert "Cleanup failed" in result["cleanup_warning"]
            assert "cleanup_success" not in result
    
    @pytest.mark.asyncio
    async def test_workflow_invalid_path(self):
        """Test workflow with invalid worktree path."""
        result = await finalize_worktree("/nonexistent/path")
        
        assert result["status"] == "failed"
        assert "Invalid worktree path" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_auto_generated_pr_content(self, temp_worktree):
        """Test workflow with auto-generated PR title and body."""
        with patch('plans.worktree.commit_worktree_changes') as mock_commit, \
             patch('plans.worktree.push_feature_branch') as mock_push, \
             patch('plans.worktree.create_pull_request') as mock_pr:
            
            mock_commit.return_value = {
                "status": "success", 
                "commit_sha": "abc123",
                "files_changed": 3
            }
            mock_push.return_value = {"status": "success", "branch_name": "feature/auto-test"}
            mock_pr.return_value = {"status": "success", "pr_url": "https://github.com/user/repo/pull/999"}
            
            result = await finalize_worktree(
                str(temp_worktree),
                pr_title="",  # Empty to trigger auto-generation
                pr_body=""    # Empty to trigger auto-generation
            )
            
            assert result["status"] == "success"
            
            # Verify auto-generated content was passed to create_pull_request
            mock_pr.assert_called_once()
            call_args = mock_pr.call_args[0]
            pr_title = call_args[1]
            pr_body = call_args[2]
            
            assert temp_worktree.name in pr_title
            assert "feature/auto-test" in pr_body
            assert "abc123" in pr_body
            assert "🤖 Generated with Claude Code" in pr_body


class TestErrorHandling:
    """Test various error scenarios."""
    
    @pytest.mark.asyncio
    async def test_unexpected_exception(self, temp_worktree):
        """Test handling of unexpected exceptions."""
        with patch('plans.worktree.validate_worktree_path', side_effect=Exception("Unexpected error")):
            result = await finalize_worktree(str(temp_worktree))
            
            assert result["status"] == "failed"
            assert "Unexpected error during finalization" in result["error"]
            assert "Unexpected error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])