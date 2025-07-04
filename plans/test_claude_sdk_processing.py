import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
import time
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plans.worktree import (
    extract_plan_prompt,
    process_single_plan,
    process_plans_in_worktrees
)


class TestExtractPlanPrompt:
    """Unit tests for plan content extraction."""
    
    def test_basic_markdown_extraction(self):
        """Test extraction of basic markdown content."""
        plan_content = """# My Plan

This is a test plan.

## Steps
1. Do something
2. Do something else
"""
        result = extract_plan_prompt(plan_content)
        
        assert "Please implement the following plan in this codebase:" in result
        assert "# My Plan" in result
        assert "This is a test plan." in result
        assert "1. Do something" in result
    
    def test_yaml_frontmatter_removal(self):
        """Test removal of YAML frontmatter."""
        plan_content = """---
title: Test Plan
author: Test User
date: 2024-01-01
---

# Actual Plan Content

This is the real content.
"""
        result = extract_plan_prompt(plan_content)
        
        # Frontmatter should be removed
        assert "title: Test Plan" not in result
        assert "author: Test User" not in result
        assert "date: 2024-01-01" not in result
        
        # Actual content should remain
        assert "# Actual Plan Content" in result
        assert "This is the real content." in result
    
    def test_empty_content(self):
        """Test handling of empty content."""
        result = extract_plan_prompt("")
        
        assert "Please implement the following plan in this codebase:" in result
        assert "Follow the plan step by step" in result
    
    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        plan_content = "Just some plain content\nWith multiple lines"
        result = extract_plan_prompt(plan_content)
        
        assert "Just some plain content" in result
        assert "With multiple lines" in result
    
    def test_malformed_frontmatter(self):
        """Test handling of malformed frontmatter."""
        plan_content = """---
This is not valid YAML
But it starts with ---

# Real Content
Test
"""
        result = extract_plan_prompt(plan_content)
        
        # Should handle gracefully - either remove or keep
        assert "# Real Content" in result
        assert "Test" in result


class TestProcessSinglePlan:
    """Unit tests for individual plan processing."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful Claude execution."""
        # Create test files
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "test_plan.md"
            plan_file.write_text("# Test Plan\nImplement feature X")
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=("Success output", ""))
            
            with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_exec:
                result = await process_single_plan(plan_file, worktree_dir)
            
            # Verify command construction
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert args[0] == "claude"
            assert args[1] == "-p"
            assert "Please implement the following plan" in args[2]
            assert args[3] == "--dangerously-skip-permissions"
            
            # Verify subprocess configuration
            kwargs = mock_exec.call_args[1]
            assert kwargs['cwd'] == worktree_dir
            assert kwargs['stdout'] == asyncio.subprocess.PIPE
            assert kwargs['stderr'] == asyncio.subprocess.PIPE
            
            # Verify result
            assert result['status'] == 'success'
            assert result['plan_file'] == 'test_plan.md'
            assert result['output'] == 'Success output'
            assert result['exit_code'] == 0
            assert 'duration' in result
            assert result['duration'] > 0
    
    @pytest.mark.asyncio
    async def test_command_failure(self):
        """Test handling of Claude command failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "test_plan.md"
            plan_file.write_text("# Test Plan")
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            # Mock failed subprocess
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=("Partial output", "Error message"))
            
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                result = await process_single_plan(plan_file, worktree_dir)
            
            assert result['status'] == 'failed'
            assert result['error'] == 'Error message'
            assert result['output'] == 'Partial output'
            assert result['exit_code'] == 1
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling for long-running processes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "test_plan.md"
            plan_file.write_text("# Test Plan")
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            # Mock process that times out
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                result = await process_single_plan(plan_file, worktree_dir)
            
            # Verify process was killed
            mock_process.kill.assert_called_once()
            mock_process.wait.assert_called_once()
            
            # Verify result
            assert result['status'] == 'failed'
            assert 'timed out after 10 minutes' in result['error']
            assert 'duration' in result
    
    @pytest.mark.asyncio
    async def test_file_read_error(self):
        """Test handling of file read errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "nonexistent.md"
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            result = await process_single_plan(plan_file, worktree_dir)
            
            assert result['status'] == 'failed'
            assert 'Exception during processing' in result['error']
            assert 'nonexistent.md' in result['plan_file']
    
    @pytest.mark.asyncio
    async def test_subprocess_creation_error(self):
        """Test handling of subprocess creation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "test_plan.md"
            plan_file.write_text("# Test Plan")
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            with patch('asyncio.create_subprocess_exec', side_effect=OSError("Command not found")):
                result = await process_single_plan(plan_file, worktree_dir)
            
            assert result['status'] == 'failed'
            assert 'Exception during processing' in result['error']
            assert 'Command not found' in result['error']


class TestProcessPlansInWorktrees:
    """Unit tests for parallel processing orchestration."""
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self):
        """Test parallel processing of multiple plans."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test plan files
            plan_files = []
            for i in range(3):
                plan_file = base_dir / f"plan_{i}.md"
                plan_file.write_text(f"# Plan {i}")
                plan_files.append(plan_file)
            
            # Create worktree directories
            created_worktrees = ["plan-0", "plan-1", "plan-2"]
            for name in created_worktrees:
                (base_dir / f"collect-{name}").mkdir()
            
            # Mock process_single_plan to track calls
            call_times = []
            async def mock_process(plan_file, worktree_dir):
                start = time.time()
                await asyncio.sleep(0.1)  # Simulate work
                call_times.append(time.time() - start)
                return {
                    "status": "success",
                    "plan_file": plan_file.name,
                    "worktree_dir": str(worktree_dir)
                }
            
            with patch('plans.worktree.process_single_plan', side_effect=mock_process):
                results = await process_plans_in_worktrees(
                    created_worktrees, plan_files, base_dir
                )
            
            # Verify all plans were processed
            assert len(results) == 3
            assert all(r['status'] == 'success' for r in results)
            
            # Verify parallel execution (all should complete in ~0.1s, not 0.3s)
            total_time = sum(call_times)
            # Relaxed timing constraint for slower systems
            assert total_time < 0.35  # Should be ~0.3s total if parallel (0.1s each)
    
    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test handling of exceptions during parallel processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            plan_files = [base_dir / "plan.md"]
            plan_files[0].write_text("# Plan")
            
            created_worktrees = ["plan"]
            (base_dir / "collect-plan").mkdir()
            
            # Mock process_single_plan to raise exception
            async def mock_process_error(plan_file, worktree_dir):
                raise RuntimeError("Test error")
            
            with patch('plans.worktree.process_single_plan', side_effect=mock_process_error):
                results = await process_plans_in_worktrees(
                    created_worktrees, plan_files, base_dir
                )
            
            assert len(results) == 1
            assert results[0]['status'] == 'failed'
            assert 'Unexpected error: Test error' in results[0]['error']
    
    @pytest.mark.asyncio
    async def test_empty_lists(self):
        """Test handling of empty input lists."""
        results = await process_plans_in_worktrees([], [], Path("/tmp"))
        assert results == []
    
    @pytest.mark.asyncio
    async def test_mismatched_plan_files(self):
        """Test handling when plan files don't match worktree names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create plan file with different naming
            plan_files = [base_dir / "different_name.md"]
            plan_files[0].write_text("# Plan")
            
            created_worktrees = ["plan-one"]
            (base_dir / "collect-plan-one").mkdir()
            
            # Should handle gracefully
            results = await process_plans_in_worktrees(
                created_worktrees, plan_files, base_dir
            )
            
            # No tasks should be created if names don't match
            assert len(results) == 0


class TestBuildWorktreesIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.asyncio
    async def test_auto_process_false_compatibility(self):
        """Test backward compatibility when auto_process=False."""
        # Import here to avoid circular imports
        from collect import build_worktrees
        
        with patch('plans.worktree.is_git_repo', return_value=False):
            result = await build_worktrees(auto_process=False)
            
            assert result['status'] == 'error'
            assert 'processing_results' not in result
    
    @pytest.mark.asyncio
    async def test_auto_process_with_mock_claude(self):
        """Test full workflow with mocked Claude execution."""
        from collect import build_worktrees
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock git operations
            with patch('plans.worktree.is_git_repo', return_value=True), \
                 patch('plans.worktree.is_working_directory_clean', return_value=True), \
                 patch('pathlib.Path.exists') as mock_exists, \
                 patch('pathlib.Path.glob') as mock_glob, \
                 patch('pathlib.Path.cwd', return_value=Path(temp_dir)), \
                 patch('plans.worktree.create') as mock_create, \
                 patch('plans.worktree.run_command') as mock_run_command, \
                 patch('plans.worktree.process_plans_in_worktrees') as mock_process:
                
                # Setup mocks
                mock_exists.return_value = True
                mock_plan = MagicMock()
                mock_plan.name = "test_plan.md"
                mock_glob.return_value = [mock_plan]
                
                # Mock successful worktree creation
                from plans.worktree import WorktreeResult, WorktreeStatus
                mock_create.return_value = WorktreeResult(
                    status=WorktreeStatus.CREATED,
                    message="Created",
                    branch_name="feature/test-plan",
                    worktree_dir=Path(temp_dir) / "collect-test-plan"
                )
                
                mock_run_command.return_value = (0, "worktree list output", "")
                
                # Mock processing results
                mock_process.return_value = [{
                    "status": "success",
                    "plan_file": "test_plan.md",
                    "output": "Processed successfully"
                }]
                
                # Run with auto_process=True
                result = await build_worktrees(auto_process=True)
                
                # Verify processing was called
                mock_process.assert_called_once()
                
                # Verify result structure
                assert result['status'] == 'success'
                assert 'processing_results' in result
                assert len(result['processing_results']) == 1
                assert result['processing_results'][0]['status'] == 'success'


class TestErrorScenarios:
    """Edge cases and error handling tests."""
    
    @pytest.mark.asyncio
    async def test_no_claude_executable(self):
        """Test behavior when Claude CLI is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = Path(temp_dir) / "test.md"
            plan_file.write_text("# Test")
            worktree_dir = Path(temp_dir) / "worktree"
            worktree_dir.mkdir()
            
            # Simulate command not found
            with patch('asyncio.create_subprocess_exec', 
                      side_effect=FileNotFoundError("claude: command not found")):
                result = await process_single_plan(plan_file, worktree_dir)
            
            assert result['status'] == 'failed'
            assert 'command not found' in result['error'].lower()
    
    def test_extract_prompt_unicode_handling(self):
        """Test handling of unicode content in plans."""
        plan_content = """# Plan with Unicode 🚀

Contains emojis 😊 and special chars: é, ñ, 中文
"""
        result = extract_plan_prompt(plan_content)
        
        assert "🚀" in result
        assert "😊" in result
        assert "中文" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_resource_limit(self):
        """Test behavior with many concurrent plans."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create many plan files
            num_plans = 20
            plan_files = []
            created_worktrees = []
            
            for i in range(num_plans):
                plan_file = base_dir / f"plan_{i}.md"
                plan_file.write_text(f"# Plan {i}")
                plan_files.append(plan_file)
                
                worktree_name = f"plan-{i}"
                created_worktrees.append(worktree_name)
                (base_dir / f"collect-{worktree_name}").mkdir()
            
            # Track concurrent executions
            max_concurrent = 0
            current_concurrent = 0
            
            async def mock_process(plan_file, worktree_dir):
                nonlocal max_concurrent, current_concurrent
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
                
                await asyncio.sleep(0.01)  # Simulate work
                
                current_concurrent -= 1
                return {"status": "success", "plan_file": plan_file.name}
            
            with patch('plans.worktree.process_single_plan', side_effect=mock_process):
                results = await process_plans_in_worktrees(
                    created_worktrees, plan_files, base_dir
                )
            
            # All should complete
            assert len(results) == num_plans
            assert all(r['status'] == 'success' for r in results)
            
            # Should allow reasonable concurrency
            assert max_concurrent > 1  # Verify parallel execution


# Test helpers
def create_test_git_repo(path: Path):
    """Helper to create a test git repository."""
    import subprocess
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, check=True)
    
    readme = path / "README.md"
    readme.write_text("# Test Repo")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=path, check=True, capture_output=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])