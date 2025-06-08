import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock
from reviewer.code_review import CodeReviewer
from llmrunner import LLMRunnerResults, ModelResult


# Module-level fixtures available to all test classes
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def reviewer(temp_dir):
    """Create a CodeReviewer instance with temp directory."""
    return CodeReviewer(output_dir=temp_dir)


@pytest.fixture
def sample_diff_content():
    """Sample diff content for testing."""
    return """
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,6 @@
 def hello():
-    print("Hello")
+    print("Hello World")
+    return "greeting"
+
+def goodbye():
+    print("Goodbye")
"""


@pytest.fixture
def mock_model_result():
    """Create a mock successful model result."""
    return ModelResult(
        model="test-model",
        timestamp="2024-01-01T12:00:00",
        success=True,
        actual_model="test-model",
        duration_seconds=2.5,
        response={
            "choices": [
                {
                    "message": {
                        "content": "# Code Review\n\nThis is a test review response."
                    }
                }
            ]
        },
    )


@pytest.fixture
def mock_failed_result():
    """Create a mock failed model result."""
    return ModelResult(
        model="failed-model",
        timestamp="2024-01-01T12:00:00",
        success=False,
        error="API timeout error",
    )


@pytest.fixture
def mock_llm_results(mock_model_result, mock_failed_result):
    """Create mock LLMRunnerResults."""
    return LLMRunnerResults(
        successful_results=[mock_model_result],
        failed_results=[mock_failed_result],
        total_models=2,
        success_count=1,
        failure_count=1,
    )


class TestCodeReviewer:
    """Test suite for CodeReviewer class."""


class TestInitialization:
    """Test CodeReviewer initialization."""

    def test_default_initialization(self):
        """Test CodeReviewer with default parameters."""
        reviewer = CodeReviewer()
        assert reviewer.output_dir == "codereview"

    def test_custom_output_dir(self):
        """Test CodeReviewer with custom output directory."""
        custom_dir = "/tmp/custom_reviews"
        reviewer = CodeReviewer(output_dir=custom_dir)
        assert reviewer.output_dir == custom_dir


class TestExtractResponseText:
    """Test response text extraction from different model formats."""

    def test_extract_gemini_response(self, reviewer):
        """Test extracting text from Gemini response format."""
        gemini_response = {
            "candidates": [
                {"content": {"parts": [{"text": "This is a Gemini response"}]}}
            ]
        }
        result = reviewer.extract_response_text(gemini_response)
        assert result == "This is a Gemini response"

    def test_extract_openai_response(self, reviewer):
        """Test extracting text from OpenAI/XAI response format."""
        openai_response = {
            "choices": [{"message": {"content": "This is an OpenAI response"}}]
        }
        result = reviewer.extract_response_text(openai_response)
        assert result == "This is an OpenAI response"

    def test_extract_anthropic_response(self, reviewer):
        """Test extracting text from Anthropic response format."""
        anthropic_response = {"content": [{"text": "This is an Anthropic response"}]}
        result = reviewer.extract_response_text(anthropic_response)
        assert result == "This is an Anthropic response"

    def test_extract_non_dict_response(self, reviewer):
        """Test extracting text from non-dictionary response."""
        simple_response = "Simple string response"
        result = reviewer.extract_response_text(simple_response)
        assert result == "Simple string response"

    def test_extract_unknown_format(self, reviewer):
        """Test extracting text from unknown response format."""
        unknown_response = {"unknown": "format"}
        result = reviewer.extract_response_text(unknown_response)
        assert result == str(unknown_response)

    def test_extract_empty_gemini_response(self, reviewer):
        """Test extracting from empty Gemini response."""
        empty_response = {"candidates": []}
        result = reviewer.extract_response_text(empty_response)
        assert result == str(empty_response)


class TestMarkdownContent:
    """Test markdown content creation."""

    def test_create_markdown_content(self, reviewer, mock_model_result):
        """Test creating markdown content for a model result."""
        response_text = "Test review content"
        result = reviewer.create_markdown_content(mock_model_result, response_text)

        assert "# Code Review - test-model" in result
        assert "**Model**: test-model" in result
        assert "**Timestamp**: 2024-01-01T12:00:00" in result
        assert "**Duration**: 2.50 seconds" in result
        assert "Test review content" in result
        assert "*Generated by test-model via MCP Code Review Tool*" in result


class TestFileOperations:
    """Test file reading and writing operations."""

    def test_read_input_file_success(self, reviewer, temp_dir, sample_diff_content):
        """Test successfully reading an input file."""
        test_file = os.path.join(temp_dir, "test_diff.md")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(sample_diff_content)

        result = reviewer.read_input_file(test_file)
        assert result == sample_diff_content

    def test_read_input_file_not_found(self, reviewer):
        """Test reading a non-existent file."""
        with pytest.raises(FileNotFoundError, match="Input file .* not found"):
            reviewer.read_input_file("/nonexistent/file.md")

    def test_write_error_file(self, reviewer, temp_dir, mock_failed_result):
        """Test writing error file for failed results."""
        timestamp = "20240101_120000"
        failed_results = [mock_failed_result]

        error_filename = reviewer.write_error_file(temp_dir, timestamp, failed_results)

        assert error_filename == "errors_20240101_120000.md"
        error_path = os.path.join(temp_dir, error_filename)
        assert os.path.exists(error_path)

        with open(error_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# Code Review Errors" in content
        assert "**Failed Models**: 1" in content
        assert "### failed-model" in content
        assert "API timeout error" in content

    def test_write_summary_file(self, reviewer, temp_dir):
        """Test writing summary JSON file."""
        timestamp = "20240101_120000"
        summary = {
            "timestamp": timestamp,
            "input_file": "test.md",
            "total_models": 2,
            "successful_reviews": 1,
            "failed_reviews": 1,
            "output_files": ["model1_20240101_120000.md"],
        }

        summary_filename = reviewer.write_summary_file(temp_dir, timestamp, summary)

        assert summary_filename == "summary_20240101_120000.json"
        summary_path = os.path.join(temp_dir, summary_filename)
        assert os.path.exists(summary_path)

        with open(summary_path, "r", encoding="utf-8") as f:
            loaded_summary = json.load(f)

        assert loaded_summary == summary


class TestPromptCreation:
    """Test code review prompt creation."""

    def test_create_code_review_prompt(self, reviewer, sample_diff_content):
        """Test creating a comprehensive code review prompt."""
        prompt = reviewer.create_code_review_prompt(sample_diff_content)

        assert "comprehensive code review" in prompt
        assert sample_diff_content in prompt
        assert "Overall Assessment" in prompt
        assert "Issues Found" in prompt
        assert "Suggestions" in prompt
        assert "Positive Aspects" in prompt
        assert "Risk Assessment" in prompt


class TestSummaryCreation:
    """Test summary creation and management."""

    def test_create_summary(self, reviewer, mock_llm_results):
        """Test creating a summary dictionary."""
        timestamp = "20240101_120000"
        from_file = "test.md"

        summary = reviewer.create_summary(timestamp, from_file, mock_llm_results)

        expected_summary = {
            "timestamp": timestamp,
            "input_file": from_file,
            "total_models": 2,
            "successful_reviews": 1,
            "failed_reviews": 1,
            "output_files": [],
        }

        assert summary == expected_summary

    def test_write_successful_results(self, reviewer, temp_dir, mock_llm_results):
        """Test writing successful model results to files."""
        timestamp = "20240101_120000"
        summary = {"output_files": []}

        reviewer.write_successful_results(
            mock_llm_results, temp_dir, timestamp, summary
        )

        # Check that file was created
        expected_filename = "test-model_20240101_120000.md"
        expected_path = os.path.join(temp_dir, expected_filename)
        assert os.path.exists(expected_path)

        # Check that summary was updated
        assert expected_filename in summary["output_files"]

        # Check file content
        with open(expected_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# Code Review - test-model" in content
        assert "This is a test review response." in content


class TestReviewCode:
    """Test the main review_code method."""

    @pytest.mark.asyncio
    async def test_review_code_success(
        self, reviewer, temp_dir, sample_diff_content, mock_llm_results
    ):
        """Test successful code review execution."""
        # Create input file
        input_file = os.path.join(temp_dir, "input_diff.md")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(sample_diff_content)

        # Mock dependencies
        with (
            patch("reviewer.code_review.code_review_models_to_mcp") as mock_models,
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_runner,
            patch("reviewer.code_review.datetime") as mock_datetime,
        ):

            mock_models.return_value = Mock()
            mock_runner.return_value = mock_llm_results
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            result = await reviewer.review_code(input_file, temp_dir)

            # Verify result structure
            assert result["status"] == "completed"
            assert result["output_directory"] == temp_dir
            # 1 success + 1 error + 1 summary
            assert result["files_created"] == 3

            # Verify files were created
            assert os.path.exists(
                os.path.join(temp_dir, "test-model_20240101_120000.md")
            )
            assert os.path.exists(os.path.join(temp_dir, "errors_20240101_120000.md"))
            assert os.path.exists(
                os.path.join(temp_dir, "summary_20240101_120000.json")
            )

    @pytest.mark.asyncio
    async def test_review_code_file_not_found(self, reviewer, temp_dir):
        """Test review_code with non-existent input file."""
        with pytest.raises(FileNotFoundError):
            await reviewer.review_code("/nonexistent/file.md", temp_dir)

    @pytest.mark.asyncio
    async def test_review_code_no_failures(
        self, reviewer, temp_dir, sample_diff_content
    ):
        """Test review_code with only successful results."""
        input_file = os.path.join(temp_dir, "input_diff.md")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(sample_diff_content)

        # Create results with no failures
        success_only_results = LLMRunnerResults(
            successful_results=[
                ModelResult(
                    model="test-model",
                    timestamp="2024-01-01T12:00:00",
                    success=True,
                    actual_model="test-model",
                    duration_seconds=2.5,
                    response={"choices": [{"message": {"content": "Review content"}}]},
                )
            ],
            failed_results=[],
            total_models=1,
            success_count=1,
            failure_count=0,
        )

        with (
            patch("reviewer.code_review.code_review_models_to_mcp") as mock_models,
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_runner,
            patch("reviewer.code_review.datetime") as mock_datetime,
        ):

            mock_models.return_value = Mock()
            mock_runner.return_value = success_only_results
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            result = await reviewer.review_code(input_file, temp_dir)

            # 1 success + 1 summary (no error file)
            assert result["files_created"] == 2
            assert "error_file" not in result["summary"]


class TestReviewDiffFromGit:
    """Test git diff review functionality."""

    @pytest.mark.asyncio
    async def test_review_diff_from_git_staged(
        self, reviewer, temp_dir, mock_llm_results
    ):
        """Test reviewing staged git diff."""
        mock_git_output = "diff --git a/file.py b/file.py\n+added line"

        with (
            patch("subprocess.run") as mock_subprocess,
            patch("reviewer.code_review.code_review_models_to_mcp") as mock_models,
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_runner,
            patch("reviewer.code_review.datetime") as mock_datetime,
        ):

            # Setup mocks
            mock_subprocess.return_value.stdout = mock_git_output
            mock_subprocess.return_value.check_returncode = Mock()
            mock_models.return_value = Mock()
            mock_runner.return_value = mock_llm_results
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            result = await reviewer.review_diff_from_git(temp_dir, staged_only=True)

            # Verify subprocess call
            mock_subprocess.assert_called_once_with(
                ["git", "diff", "--staged"], capture_output=True, text=True, check=True
            )

            # Verify result
            assert result["status"] == "completed"
            assert result["summary"]["source"] == "git_diff_staged"
            assert result["summary"]["input_file"] == "git diff"

    @pytest.mark.asyncio
    async def test_review_diff_from_git_all_changes(
        self, reviewer, temp_dir, mock_llm_results
    ):
        """Test reviewing all git changes."""
        mock_git_output = "diff --git a/file.py b/file.py\n+added line"

        with (
            patch("subprocess.run") as mock_subprocess,
            patch("reviewer.code_review.code_review_models_to_mcp") as mock_models,
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_runner,
            patch("reviewer.code_review.datetime") as mock_datetime,
        ):

            mock_subprocess.return_value.stdout = mock_git_output
            mock_subprocess.return_value.check_returncode = Mock()
            mock_models.return_value = Mock()
            mock_runner.return_value = mock_llm_results
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            result = await reviewer.review_diff_from_git(temp_dir, staged_only=False)

            mock_subprocess.assert_called_once_with(
                ["git", "diff"], capture_output=True, text=True, check=True
            )

            assert result["summary"]["source"] == "git_diff_all"

    @pytest.mark.asyncio
    async def test_review_diff_no_changes(self, reviewer, temp_dir):
        """Test git diff with no changes."""
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.stdout = ""
            mock_subprocess.return_value.check_returncode = Mock()

            with pytest.raises(ValueError, match="No changes found in git diff"):
                await reviewer.review_diff_from_git(temp_dir)

    @pytest.mark.asyncio
    async def test_review_diff_git_not_found(self, reviewer, temp_dir):
        """Test git diff when git is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            with pytest.raises(Exception, match="Git not found"):
                await reviewer.review_diff_from_git(temp_dir)

    @pytest.mark.asyncio
    async def test_review_diff_git_error(self, reviewer, temp_dir):
        """Test git diff with git command error."""
        import subprocess

        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            with pytest.raises(Exception, match="Git diff failed"):
                await reviewer.review_diff_from_git(temp_dir)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_response_malformed_gemini(self, reviewer):
        """Test extracting from malformed Gemini response."""
        malformed = {"candidates": [{"content": {"parts": []}}]}  # Empty parts
        result = reviewer.extract_response_text(malformed)
        assert result == str(malformed)

    def test_extract_response_malformed_openai(self, reviewer):
        """Test extracting from malformed OpenAI response."""
        malformed = {"choices": [{"message": {}}]}  # Missing content
        result = reviewer.extract_response_text(malformed)
        assert result == ""

    def test_extract_response_empty_anthropic(self, reviewer):
        """Test extracting from empty Anthropic response."""
        empty = {"content": []}
        result = reviewer.extract_response_text(empty)
        assert result == str(empty)

    @pytest.mark.asyncio
    async def test_review_code_with_default_output_dir(
        self, reviewer, temp_dir, sample_diff_content
    ):
        """Test review_code using default output directory from None."""
        input_file = os.path.join(temp_dir, "input_diff.md")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(sample_diff_content)

        success_results = LLMRunnerResults(
            successful_results=[],
            failed_results=[],
            total_models=0,
            success_count=0,
            failure_count=0,
        )

        with (
            patch("reviewer.code_review.code_review_models_to_mcp") as mock_models,
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_runner,
            patch("reviewer.code_review.datetime") as mock_datetime,
            patch("os.makedirs") as mock_makedirs,
        ):

            mock_models.return_value = Mock()
            mock_runner.return_value = success_results
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            # Test with None to_file (should use default)
            result = await reviewer.review_code(input_file, None)

            # Should use reviewer's default output_dir
            mock_makedirs.assert_called_with(temp_dir, exist_ok=True)
            assert result["output_directory"] == temp_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
