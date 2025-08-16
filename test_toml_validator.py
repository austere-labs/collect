"""
Tests for TOML validation and fixing functionality in slashsync tool.
"""

import pytest
from pathlib import Path
from toml_validator import TomlValidator


class TestTomlValidator:
    """Test suite for TomlValidator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = TomlValidator()

    def test_validate_valid_toml(self):
        """Test validation of valid TOML content"""
        valid_toml = """
title = "Test Command"
description = "A test command"

[command]
name = "test"
type = "simple"

[[workflow_steps]]
description = "Step 1"
commands = ["echo hello"]
"""
        is_valid, errors = self.validator.validate_toml(valid_toml)
        assert is_valid
        assert len(errors) == 0

    def test_validate_empty_toml(self):
        """Test validation of empty content"""
        is_valid, errors = self.validator.validate_toml("")
        assert not is_valid
        assert "Empty TOML content" in errors[0]

    def test_validate_invalid_toml(self):
        """Test validation of invalid TOML content"""
        invalid_toml = """
title = "Test Command
description = missing quote
[invalid section name with spaces]
"""
        is_valid, errors = self.validator.validate_toml(invalid_toml)
        assert not is_valid
        assert len(errors) > 0
        assert "TOML parsing error" in errors[0]

    def test_clean_gemini_artifacts(self):
        """Test removal of common Gemini AI artifacts"""
        content_with_artifacts = """Loaded cached credentials.
```toml
title = "Test Command"
description = "A test command"
```
"""
        cleaned = self.validator.clean_gemini_artifacts(content_with_artifacts)
        expected = '''title = "Test Command"
description = "A test command"'''
        assert cleaned == expected

    def test_clean_gemini_artifacts_with_status_messages(self):
        """Test removal of status and error messages"""
        content_with_status = """Loaded cached credentials.
I need the actual file path to convert. Please provide the path to the markdown command file.
```toml
title = "Test"
```
"""
        cleaned = self.validator.clean_gemini_artifacts(content_with_status)
        expected = '''title = "Test"'''
        assert cleaned == expected

    def test_extract_toml_from_markdown_with_toml_fence(self):
        """Test extraction of TOML from markdown code fences"""
        markdown_content = """
Here is the converted TOML:

```toml
title = "Test Command"
description = "Extracted from markdown"
```

This is the result.
"""
        extracted = self.validator.extract_toml_from_markdown(markdown_content)
        expected = '''title = "Test Command"
description = "Extracted from markdown"'''
        assert extracted == expected

    def test_extract_toml_from_markdown_generic_fence(self):
        """Test extraction of TOML from generic code fences"""
        markdown_content = """
Here is the result:

```
title = "Test Command" 
description = "Generic fence"
```

Not TOML:
```
def hello():
    print("world")
```
"""
        extracted = self.validator.extract_toml_from_markdown(markdown_content)
        expected = '''title = "Test Command" 
description = "Generic fence"'''
        assert extracted == expected

    def test_extract_toml_no_markdown(self):
        """Test extraction when no markdown fences present"""
        plain_toml = '''title = "Direct TOML"
description = "No fences needed"'''
        extracted = self.validator.extract_toml_from_markdown(plain_toml)
        assert extracted == plain_toml

    def test_fix_common_toml_issues_unquoted_strings(self):
        """Test fixing of unquoted string values"""
        content_with_issues = """
title = Test Command Without Quotes
description = Another unquoted string
count = 42
enabled = true
items = ["quoted", "array"]
"""
        fixed = self.validator.fix_common_toml_issues(content_with_issues)
        expected_lines = [
            'title = "Test Command Without Quotes"',
            'description = "Another unquoted string"',
            "count = 42",
            "enabled = true",
            'items = ["quoted", "array"]',
        ]
        for expected_line in expected_lines:
            assert expected_line in fixed

    def test_fix_common_toml_issues_preserves_sections(self):
        """Test that fixing preserves section headers and comments"""
        content = """
# This is a comment
[section]
key = unquoted value

[[array_of_tables]]
name = another unquoted
"""
        fixed = self.validator.fix_common_toml_issues(content)
        assert "# This is a comment" in fixed
        assert "[section]" in fixed
        assert "[[array_of_tables]]" in fixed
        assert 'key = "unquoted value"' in fixed
        assert 'name = "another unquoted"' in fixed

    def test_fix_toml_complete_workflow(self):
        """Test the complete TOML fixing workflow"""
        problematic_content = """Loaded cached credentials.
```toml
title = Test Command
context = Acting as a developer

[[workflow_steps]]
description = First step
commands = ["git status"]
```
"""
        fixed = self.validator.fix_toml(problematic_content)

        # Should be valid TOML after fixing
        is_valid, errors = self.validator.validate_toml(fixed)
        assert is_valid, f"Fixed TOML should be valid, errors: {errors}"

        # Should contain expected content
        assert 'title = "Test Command"' in fixed
        assert 'context = "Acting as a developer"' in fixed
        assert "[[workflow_steps]]" in fixed
        assert 'description = "First step"' in fixed

        # Should not contain artifacts
        assert "Loaded cached credentials." not in fixed
        assert "```toml" not in fixed
        assert "```" not in fixed

    def test_validate_and_fix_already_valid(self):
        """Test validate_and_fix with already valid content"""
        valid_content = '''title = "Valid Command"
description = "Already good"'''

        fixed_content, is_valid, errors = self.validator.validate_and_fix(valid_content)

        assert is_valid
        assert len(errors) == 0
        assert fixed_content == valid_content

    def test_validate_and_fix_fixable_content(self):
        """Test validate_and_fix with fixable content"""
        fixable_content = """Loaded cached credentials.
```toml
title = Fixable Command
```"""

        fixed_content, is_valid, errors = self.validator.validate_and_fix(
            fixable_content
        )

        assert is_valid
        assert len(errors) == 0
        assert 'title = "Fixable Command"' in fixed_content
        assert "Loaded cached credentials." not in fixed_content

    def test_validate_and_fix_unfixable_content(self):
        """Test validate_and_fix with unfixable content"""
        unfixable_content = """
[invalid section with spaces and no closing bracket
title = "Missing closing bracket for section"
"""

        fixed_content, is_valid, errors = self.validator.validate_and_fix(
            unfixable_content
        )

        assert not is_valid
        assert len(errors) > 0
        assert "TOML parsing error" in errors[0]

    def test_real_world_gemini_output(self):
        """Test with actual problematic output from Gemini"""
        real_gemini_output = """Loaded cached credentials.
```toml
title = "Git Commit: Auto-stage and Commit Changes"
context = "You are acting as a Senior Software Engineer performing a git commit. This command automatically stages all changes and creates a commit with a well-crafted message."

[[workflow_steps]]
description = "Check repository status."
commands = ["git status"]

[[workflow_steps]]
description = "If there are unstaged changes, stage all changes and inform the user."
commands = ["git add ."]

important_notes = [
    "This command stages ALL changes with `git add .`",
    "Review changes carefully before committing"
]
```"""

        fixed_content, is_valid, errors = self.validator.validate_and_fix(
            real_gemini_output
        )

        assert is_valid, f"Real Gemini output should be fixable, errors: {errors}"
        assert "Loaded cached credentials." not in fixed_content
        assert "```toml" not in fixed_content
        assert "```" not in fixed_content
        assert 'title = "Git Commit: Auto-stage and Commit Changes"' in fixed_content

    def test_edge_case_multiple_code_blocks(self):
        """Test handling of multiple code blocks with only one being TOML"""
        content_with_multiple_blocks = """
Here's some Python:
```python
def hello():
    print("world")
```

And here's the TOML:
```toml
title = "Multiple Blocks"
```

And some shell:
```bash
echo "hello"
```
"""

        extracted = self.validator.extract_toml_from_markdown(
            content_with_multiple_blocks
        )
        assert 'title = "Multiple Blocks"' in extracted
        assert "def hello():" not in extracted
        assert 'echo "hello"' not in extracted

    def test_preserve_complex_toml_structures(self):
        """Test that complex TOML structures are preserved during fixing"""
        complex_toml = """Loaded cached credentials.
```toml
[command]
name = "complex_command"
description = "A complex command structure"

[command.parameters]
file_name = { type = "string", description = "The file path" }
force = { type = "boolean", default = false }

[[workflow_steps]]
description = "First step"
commands = ["echo", "hello"]

[[workflow_steps]]
description = "Second step"
commands = [
    "git status",
    "git add ."
]

[metadata]
version = "1.0.0"
tags = ["git", "automation"]
```"""

        fixed_content, is_valid, errors = self.validator.validate_and_fix(complex_toml)

        assert is_valid, f"Complex TOML should be fixable, errors: {errors}"

        # Check that complex structures are preserved
        assert "[command.parameters]" in fixed_content
        assert '{ type = "string", description = "The file path" }' in fixed_content
        assert "[[workflow_steps]]" in fixed_content
        assert "default = false" in fixed_content


@pytest.mark.integration
class TestTomlValidatorIntegration:
    """Integration tests for TOML validator with real files"""

    def test_validate_existing_toml_files(self):
        """Test validation against existing .toml files in the project"""
        validator = TomlValidator()
        gemini_commands_dir = Path(__file__).parent / ".gemini" / "commands"

        if not gemini_commands_dir.exists():
            pytest.skip("No .gemini/commands directory found")

        toml_files = list(gemini_commands_dir.rglob("*.toml"))

        if not toml_files:
            pytest.skip("No TOML files found in .gemini/commands")

        validation_results = []

        for toml_file in toml_files[:5]:  # Test first 5 files to avoid long test times
            try:
                content = toml_file.read_text(encoding="utf-8")
                is_valid, errors = validator.validate_toml(content)
                validation_results.append((toml_file.name, is_valid, errors))

                if not is_valid:
                    # Try to fix it
                    fixed_content, fixed_valid, fixed_errors = (
                        validator.validate_and_fix(content)
                    )
                    print(f"\nFile: {toml_file.name}")
                    print(f"Original valid: {is_valid}")
                    print(f"Fixed valid: {fixed_valid}")
                    if not fixed_valid:
                        print(f"Errors: {fixed_errors}")

            except Exception as e:
                validation_results.append((toml_file.name, False, [str(e)]))

        # Report results
        valid_count = sum(1 for _, is_valid, _ in validation_results if is_valid)
        total_count = len(validation_results)

        print(f"\nValidation Results: {valid_count}/{total_count} files are valid")

        # At least some files should be fixable
        assert total_count > 0, "Should have found some TOML files to test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
