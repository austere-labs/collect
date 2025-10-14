import pytest
from ytreader import read_video
from config import Config
from secret_manager import SecretManager
from models import YouTubeReader


@pytest.fixture
def youtube_reader():
    """Fixture to create YouTubeReader instance"""
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    return YouTubeReader(config, secret_mgr, "gemini-2.5-flash")


@pytest.fixture
def test_video_url():
    """Fixture with a short, well-known YouTube video for testing"""
    # This is a very short video that's good for testing
    return "https://www.youtube.com/watch?v=jNQXAC9IVRw"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.mark.asyncio
async def test_read_video_with_output_file(test_video_url, temp_output_dir):
    """Test read_video with explicit output file"""
    output_file = temp_output_dir / "test_summary.md"

    # Call the function
    result = await read_video(test_video_url, str(output_file))

    # Assertions
    assert isinstance(result, str)
    assert len(result) > 0
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == result


@pytest.mark.asyncio
async def test_read_video_without_output_file(test_video_url, tmp_path):
    """Test read_video with auto-generated filename"""
    # Change to temp directory
    import os

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Call function without output file
        result = await read_video(test_video_url)

        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Check that a timestamped file was created
        md_files = list(tmp_path.glob("youtube_analysis_*.md"))
        assert len(md_files) == 1
        assert md_files[0].read_text(encoding="utf-8") == result

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_read_video_creates_parent_directories(test_video_url, tmp_path):
    """Test that read_video creates parent directories if they don't exist"""
    nested_output = tmp_path / "research" / "youtube_summaries" / "test.md"

    # Verify directory doesn't exist yet
    assert not nested_output.parent.exists()

    # Call function
    result = await read_video(test_video_url, str(nested_output))

    # Assertions
    assert isinstance(result, str)
    assert len(result) > 0
    assert nested_output.exists()
    assert nested_output.read_text(encoding="utf-8") == result
    assert nested_output.parent.exists()


@pytest.mark.asyncio
async def test_read_video_with_invalid_url(temp_output_dir):
    """Test read_video raises error with invalid YouTube URL"""
    invalid_url = "https://example.com/not-a-video"
    output_file = temp_output_dir / "test.md"

    # Call function and expect an error
    with pytest.raises(Exception):
        await read_video(invalid_url, str(output_file))


@pytest.mark.asyncio
async def test_read_video_with_utf8_content(test_video_url, temp_output_dir):
    """Test read_video handles UTF-8 content correctly"""
    output_file = temp_output_dir / "utf8_test.md"

    # Call function
    result = await read_video(test_video_url, str(output_file))

    # Assertions - verify UTF-8 encoding works
    assert isinstance(result, str)
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert content == result


@pytest.mark.asyncio
async def test_youtube_reader_validate_url(youtube_reader):
    """Test YouTube URL validation"""
    assert youtube_reader.validate_youtube_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert youtube_reader.validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert not youtube_reader.validate_youtube_url("https://example.com")


@pytest.mark.asyncio
async def test_youtube_reader_default_prompt(youtube_reader):
    """Test that YouTubeReader has a default prompt"""
    prompt = youtube_reader.get_default_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0


@pytest.mark.asyncio
async def test_read_video_returns_content(test_video_url, temp_output_dir):
    """Test that read_video returns the analyzed content"""
    output_file = temp_output_dir / "return_test.md"

    # Call function
    result = await read_video(test_video_url, str(output_file))

    # Assertions
    assert isinstance(result, str)
    assert len(result) > 0
    # The result should contain some meaningful content
    assert len(result) > 50  # Should be more than just a few words
