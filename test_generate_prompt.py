import pytest
from config import Config
from secret_manager import SecretManager
from models.anthropic_mpc import AnthropicMCP
from collect import generate_prompt


@pytest.fixture
def sample_prompt():
    """Sample prompt content for testing."""
    return """Create a helpful AI assistant that can answer programming questions.
The assistant should be knowledgeable about Python, JavaScript, and web development.
It should provide clear explanations and code examples when appropriate."""


class TestGeneratePrompt:
    
    @pytest.mark.asyncio
    async def test_generate_prompt_basic(self, sample_prompt):
        """Test basic functionality of generate_prompt."""
        # Check if we have required config
        config = Config()
        if not config.project_id or not config.anthropic_key_path:
            pytest.skip("Missing GCP_PROJECT_ID or ANTHROPIC_KEY_PATH in .env")
        
        result = await generate_prompt(sample_prompt)
        
        # Verify we got a string response
        assert isinstance(result, str)
        assert len(result) > 0
        
        # The generated prompt should contain relevant content
        # Note: We can't predict exact content, but it should be substantial
        assert len(result) > 50  # Should be more than just a few words
    
    @pytest.mark.asyncio
    async def test_generate_prompt_with_target_model(self, sample_prompt):
        """Test generate_prompt with target_model parameter."""
        config = Config()
        if not config.project_id or not config.anthropic_key_path:
            pytest.skip("Missing GCP_PROJECT_ID or ANTHROPIC_KEY_PATH in .env")
        
        result = await generate_prompt(
            sample_prompt, 
            target_model="claude-3-7-sonnet-20250219"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_prompt_empty_string(self):
        """Test error handling for empty prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await generate_prompt("")
    
    @pytest.mark.asyncio
    async def test_generate_prompt_whitespace_only(self):
        """Test error handling for whitespace-only prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await generate_prompt("   \n\t   ")
    
    @pytest.mark.asyncio
    async def test_generate_prompt_simple_task(self):
        """Test with a simple task description."""
        config = Config()
        if not config.project_id or not config.anthropic_key_path:
            pytest.skip("Missing GCP_PROJECT_ID or ANTHROPIC_KEY_PATH in .env")
        
        simple_task = "A coding assistant that helps with Python"
        result = await generate_prompt(simple_task)
        
        assert isinstance(result, str)
        assert len(result) > len(simple_task)  # Should be expanded


if __name__ == "__main__":
    # Run a simple test
    import asyncio
    
    async def manual_test():
        """Manual test function for quick verification."""
        test_prompt = "Create a Python function that validates email addresses."
        
        try:
            result = await generate_prompt(test_prompt)
            print(f"Input prompt: {test_prompt}")
            print(f"Generated prompt ({len(result)} chars):")
            print("-" * 50)
            print(result)
            print("-" * 50)
        except Exception as e:
            print(f"Error: {e}")
    
    # Uncomment to run manual test
    # asyncio.run(manual_test())