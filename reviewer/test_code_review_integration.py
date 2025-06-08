import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
from reviewer.code_review import CodeReviewer
from llmrunner import LLMRunnerResults, ModelResult


class TestCodeReviewIntegration:
    """Test integration between .claude/commands/model_code_review.md and code_review.py"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_diff_content(self):
        """Sample diff content for testing"""
        return """diff --git a/src/auth.py b/src/auth.py
index 1234567..abcdefg 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,5 +1,10 @@
 def authenticate_user(username, password):
-    # Simple authentication
-    return username == "admin" and password == "secret"
+    # Improved authentication with validation
+    if not username or not password:
+        return False
+    
+    # TODO: Add proper password hashing
+    return username == "admin" and password == "secret123"
 
 def get_user_role(username):
     return "admin" if username == "admin" else "user"
"""

    @pytest.fixture
    def sample_diff_file(self, temp_dir, sample_diff_content):
        """Create sample diff file for testing"""
        diff_file = os.path.join(temp_dir, "test_diff.md")
        with open(diff_file, "w") as f:
            f.write(sample_diff_content)
        return diff_file

    @pytest.fixture
    def mock_llm_results(self):
        """Mock LLM runner results matching expected format"""
        successful_results = [
            ModelResult(
                model="claude-3-5-sonnet",
                success=True,
                response={
                    "content": [
                        {
                            "text": "## Code Review Analysis\n\n### Security Issues\n🔴 **Critical**: Hardcoded password in authentication logic\n\n### Recommendations\n- Implement proper password hashing\n- Add input validation"
                        }
                    ]
                },
                timestamp="2024-01-01T12:00:00",
                duration_seconds=2.5,
                error=None,
            ),
            ModelResult(
                model="gpt-4-turbo",
                success=True,
                response={
                    "choices": [
                        {
                            "message": {
                                "content": "## Security Analysis\n\n🔴 **High Risk**: Authentication uses plaintext password comparison\n🟡 **Medium**: Missing input validation for empty credentials"
                            }
                        }
                    ]
                },
                timestamp="2024-01-01T12:00:05",
                duration_seconds=3.1,
                error=None,
            ),
        ]

        failed_results = [
            ModelResult(
                model="gemini-pro",
                success=False,
                response=None,
                timestamp="2024-01-01T12:00:10",
                duration_seconds=0,
                error="API rate limit exceeded",
            )
        ]

        return LLMRunnerResults(
            successful_results=successful_results,
            failed_results=failed_results,
            total_models=3,
            success_count=2,
            failure_count=1,
        )

    @pytest.mark.asyncio
    async def test_code_review_from_file_integration(
        self, temp_dir, sample_diff_file, mock_llm_results
    ):
        """Test the complete file-based code review workflow as described in Claude command"""
        with (
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_llmrunner,
            patch(
                "reviewer.code_review.code_review_models_to_mcp"
            ) as mock_models_config,
        ):

            # Setup mocks
            mock_llmrunner.return_value = mock_llm_results
            mock_models_config.return_value = {"claude": "config", "gpt": "config"}

            # Initialize reviewer with temp directory
            reviewer = CodeReviewer(output_dir=temp_dir)

            # Run review (simulates mcp__collect__run_code_review)
            result = await reviewer.review_code(sample_diff_file, temp_dir)

            # Verify return structure matches command expectations
            assert result["status"] == "completed"
            assert "summary" in result
            assert "output_directory" in result
            assert "files_created" in result

            # Verify output files were created as documented in command
            files = os.listdir(temp_dir)

            # Should have individual model reviews
            claude_files = [f for f in files if f.startswith("claude-3-5-sonnet")]
            gpt_files = [f for f in files if f.startswith("gpt-4-turbo")]
            assert len(claude_files) == 1
            assert len(gpt_files) == 1

            # Should have summary file
            summary_files = [f for f in files if f.startswith("summary_")]
            assert len(summary_files) == 1

            # Should have errors file for failed models
            error_files = [f for f in files if f.startswith("errors_")]
            assert len(error_files) == 1

            # Verify summary JSON structure
            summary_file = os.path.join(temp_dir, summary_files[0])
            with open(summary_file, "r") as f:
                summary_data = json.load(f)

            assert summary_data["total_models"] == 3
            assert summary_data["successful_reviews"] == 2
            assert summary_data["failed_reviews"] == 1
            assert len(summary_data["output_files"]) == 2

    @pytest.mark.asyncio
    async def test_git_diff_review_integration(self, temp_dir, mock_llm_results):
        """Test git diff review workflow as described in Claude command"""
        with (
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_llmrunner,
            patch(
                "reviewer.code_review.code_review_models_to_mcp"
            ) as mock_models_config,
            patch("subprocess.run") as mock_subprocess,
        ):

            # Setup mocks
            mock_llmrunner.return_value = mock_llm_results
            mock_models_config.return_value = {"claude": "config"}

            # Mock git diff output
            mock_subprocess.return_value = MagicMock(
                stdout="diff --git a/test.py b/test.py\n+def new_function():\n+    pass",
                returncode=0,
            )

            reviewer = CodeReviewer(output_dir=temp_dir)

            # Test staged-only review (Option A from command)
            result = await reviewer.review_diff_from_git(temp_dir, staged_only=True)

            # Verify subprocess called with correct git command
            mock_subprocess.assert_called_with(
                ["git", "diff", "--staged"], capture_output=True, text=True, check=True
            )

            # Verify result structure
            assert result["status"] == "completed"
            assert result["summary"]["source"] == "git_diff_staged"

            # Test all changes review
            await reviewer.review_diff_from_git(temp_dir, staged_only=False)
            mock_subprocess.assert_called_with(
                ["git", "diff"], capture_output=True, text=True, check=True
            )

    def test_claude_command_workflow_documentation(self):
        """Verify that the Claude command documentation matches code_review.py capabilities"""
        reviewer = CodeReviewer()

        # Test that CodeReviewer has methods mentioned in command
        assert hasattr(
            reviewer, "review_code"
        ), "Should support file-based review (Option B)"
        assert hasattr(
            reviewer, "review_diff_from_git"
        ), "Should support git diff review (Option A)"

        # Test that review_code signature matches command usage
        import inspect

        sig = inspect.signature(reviewer.review_code)
        assert "from_file" in sig.parameters, "Should accept from_file parameter"
        assert "to_file" in sig.parameters, "Should accept to_file parameter"

        # Test that review_diff_from_git signature matches command usage
        sig = inspect.signature(reviewer.review_diff_from_git)
        assert "staged_only" in sig.parameters, "Should accept staged_only parameter"
        assert "to_file" in sig.parameters, "Should accept to_file parameter"

    def test_output_file_naming_convention(
        self, temp_dir, sample_diff_file, mock_llm_results
    ):
        """Test that output files follow naming convention documented in command"""
        with (
            patch(
                "reviewer.code_review.llmrunner", new_callable=AsyncMock
            ) as mock_llmrunner,
            patch(
                "reviewer.code_review.code_review_models_to_mcp"
            ) as mock_models_config,
        ):

            mock_llmrunner.return_value = mock_llm_results
            mock_models_config.return_value = {}

            reviewer = CodeReviewer(output_dir=temp_dir)

            # Mock timestamp for predictable filenames
            with patch("reviewer.code_review.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20241201_143052"

                # Run async test
                import asyncio

                asyncio.run(reviewer.review_code(sample_diff_file, temp_dir))

            files = os.listdir(temp_dir)

            # Verify naming matches documentation: {model}_YYYYMMDD_HHMMSS.md
            expected_patterns = [
                "claude-3-5-sonnet_20241201_143052.md",
                "gpt-4-turbo_20241201_143052.md",
                "summary_20241201_143052.json",
                "errors_20241201_143052.md",
            ]

            for pattern in expected_patterns:
                assert pattern in files, f"Expected file {pattern} not found in {files}"

    def test_prompt_structure_matches_command_requirements(self):
        """Test that code review prompt includes all sections mentioned in command"""
        reviewer = CodeReviewer()
        prompt = reviewer.create_code_review_prompt("sample code")

        # Verify prompt includes all required sections from command documentation
        required_sections = [
            "Overall Assessment",
            "Issues Found",
            "Security vulnerabilities",
            "Bugs and logic errors",
            "Performance issues",
            "Code quality problems",
            "Testing gaps",
            "Suggestions for Improvement",
            "Positive Aspects",
            "Risk Assessment",
            "Summary Table",
        ]

        for section in required_sections:
            assert section in prompt, f"Prompt missing required section: {section}"

        # Verify emoji risk indicators are included
        risk_emojis = ["🔴", "🟡", "🟢"]
        for emoji in risk_emojis:
            assert emoji in prompt, f"Prompt missing risk emoji: {emoji}"

    @pytest.mark.asyncio
    async def test_error_handling_matches_command_expectations(self, temp_dir):
        """Test error handling for scenarios mentioned in command troubleshooting"""
        reviewer = CodeReviewer(output_dir=temp_dir)

        # Test "No git changes found" scenario
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(stdout="", returncode=0)

            with pytest.raises(ValueError, match="No changes found in git diff"):
                await reviewer.review_diff_from_git(temp_dir)

        # Test file not found scenario
        with pytest.raises(FileNotFoundError, match="Input file.*not found"):
            await reviewer.review_code("nonexistent_file.md", temp_dir)

        # Test git not available scenario
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            with pytest.raises(Exception, match="Git not found"):
                await reviewer.review_diff_from_git(temp_dir)

    def test_response_text_extraction_supports_all_models(self):
        """Test that response extraction works for all model formats mentioned in command"""
        reviewer = CodeReviewer()

        # Test Anthropic Claude format
        anthropic_response = {"content": [{"text": "Claude review content"}]}
        assert (
            reviewer.extract_response_text(anthropic_response)
            == "Claude review content"
        )

        # Test OpenAI GPT format
        openai_response = {"choices": [{"message": {"content": "GPT review content"}}]}
        assert reviewer.extract_response_text(openai_response) == "GPT review content"

        # Test Google Gemini format
        gemini_response = {
            "candidates": [{"content": {"parts": [{"text": "Gemini review content"}]}}]
        }
        assert (
            reviewer.extract_response_text(gemini_response) == "Gemini review content"
        )

        # Test fallback for XAI Grok or unknown formats
        unknown_response = "Direct string response"
        assert (
            reviewer.extract_response_text(unknown_response) == "Direct string response"
        )
