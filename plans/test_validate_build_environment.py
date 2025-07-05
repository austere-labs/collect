import pytest
from pathlib import Path
from unittest.mock import patch
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plans.worktree import validate_build_environment


class TestValidateBuildEnvironment:
    """Test the validate_build_environment function."""

    def test_not_git_repo(self):
        """Test validation when not in a git repository."""
        with patch("plans.worktree.is_git_repo", return_value=False):
            result = validate_build_environment()

            assert result["status"] == "error"
            assert result["message"] == "Not in a git repository"

    def test_uncommitted_changes(self):
        """Test validation with uncommitted changes."""
        with (
            patch("plans.worktree.is_git_repo", return_value=True),
            patch("plans.worktree.is_working_directory_clean", return_value=False),
        ):

            result = validate_build_environment()

            assert result["status"] == "warning"
            assert "uncommitted changes" in result["message"]

    def test_no_approved_dir(self):
        """Test validation when approved plans directory doesn't exist."""
        with (
            patch("plans.worktree.is_git_repo", return_value=True),
            patch("plans.worktree.is_working_directory_clean", return_value=True),
            patch("pathlib.Path.exists", return_value=False),
        ):

            result = validate_build_environment()

            assert result["status"] == "error"
            assert "_docs/plans/approved" in result["message"]
            assert "does not exist" in result["message"]

    def test_all_checks_pass(self):
        """Test validation when all checks pass."""
        with (
            patch("plans.worktree.is_git_repo", return_value=True),
            patch("plans.worktree.is_working_directory_clean", return_value=True),
            patch("pathlib.Path.exists", return_value=True),
        ):

            result = validate_build_environment()

            assert result["status"] == "success"
            assert "message" not in result

    def test_validation_order(self):
        """Test that validations happen in the correct order."""
        # First check should be git repo
        with patch("plans.worktree.is_git_repo", return_value=False):
            result = validate_build_environment()
            assert "Not in a git repository" in result["message"]

        # Second check should be working directory
        with (
            patch("plans.worktree.is_git_repo", return_value=True),
            patch("plans.worktree.is_working_directory_clean", return_value=False),
        ):
            result = validate_build_environment()
            assert "uncommitted changes" in result["message"]

        # Third check should be approved directory
        with (
            patch("plans.worktree.is_git_repo", return_value=True),
            patch("plans.worktree.is_working_directory_clean", return_value=True),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = validate_build_environment()
            assert "_docs/plans/approved" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
