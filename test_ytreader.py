import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from ytreader import read_video
from google.genai.types import GenerateContentResponse, Candidate, Content, Part


@pytest.fixture
def mock_config():
    """Mock Config object"""
    config = Mock()
    config.project_id = "test-project"
    config.gemini_model = "gemini-2.0-flash"
    return config


@pytest.fixture
def mock_secret_manager():
    """Mock SecretManager"""
    secret_mgr = Mock()
    secret_mgr.get_secret = Mock(return_value="test-api-key")
    return secret_mgr


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    # Create mock response structure
    part = Part(text="This is a test video summary about Python programming.")
    content = Content(parts=[part], role="model")
    candidate = Candidate(content=content, finish_reason=None, safety_ratings=[])

    response = Mock(spec=GenerateContentResponse)
    response.candidates = [candidate]
    return response


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.mark.asyncio
async def test_read_video_with_output_file(
    mock_config, mock_secret_manager, mock_gemini_response, temp_output_dir
):
    """Test read_video with explicit output file"""
    output_file = temp_output_dir / "test_summary.md"
    test_url = "https://youtube.com/watch?v=test123"

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=mock_gemini_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Call function
        result = await read_video(test_url, str(output_file))

        # Assertions
        assert result == "This is a test video summary about Python programming."
        assert output_file.exists()
        assert output_file.read_text() == result
        mock_yt_instance.analyze_video.assert_called_once_with(test_url, "Summarize this video")


@pytest.mark.asyncio
async def test_read_video_without_output_file(
    mock_config, mock_secret_manager, mock_gemini_response, tmp_path
):
    """Test read_video with auto-generated filename"""
    test_url = "https://youtube.com/watch?v=test456"

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=mock_gemini_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Change to temp directory
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Call function without output file
            result = await read_video(test_url)

            # Assertions
            assert result == "This is a test video summary about Python programming."

            # Check that a timestamped file was created
            md_files = list(tmp_path.glob("youtube_analysis_*.md"))
            assert len(md_files) == 1
            assert md_files[0].read_text() == result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_read_video_creates_parent_directories(
    mock_config, mock_secret_manager, mock_gemini_response, tmp_path
):
    """Test that read_video creates parent directories if they don't exist"""
    nested_output = tmp_path / "research" / "youtube_summaries" / "test.md"
    test_url = "https://youtube.com/watch?v=test789"

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=mock_gemini_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Verify directory doesn't exist yet
        assert not nested_output.parent.exists()

        # Call function
        result = await read_video(test_url, str(nested_output))

        # Assertions
        assert nested_output.exists()
        assert nested_output.read_text() == result
        assert nested_output.parent.exists()


@pytest.mark.asyncio
async def test_read_video_no_candidates_raises_error(
    mock_config, mock_secret_manager, temp_output_dir
):
    """Test that read_video raises ValueError when no candidates returned"""
    test_url = "https://youtube.com/watch?v=test404"
    output_file = temp_output_dir / "test.md"

    # Create response with no candidates
    empty_response = Mock(spec=GenerateContentResponse)
    empty_response.candidates = []

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=empty_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Call function and expect ValueError
        with pytest.raises(ValueError, match="no response from Gemini API's"):
            await read_video(test_url, str(output_file))


@pytest.mark.asyncio
async def test_read_video_with_utf8_content(
    mock_config, mock_secret_manager, temp_output_dir
):
    """Test read_video handles UTF-8 content correctly"""
    test_url = "https://youtube.com/watch?v=utf8test"
    output_file = temp_output_dir / "utf8_test.md"

    # Create response with UTF-8 content
    utf8_content = "Video summary with unicode: 你好 🎥 café"
    part = Part(text=utf8_content)
    content = Content(parts=[part], role="model")
    candidate = Candidate(content=content, finish_reason=None, safety_ratings=[])

    utf8_response = Mock(spec=GenerateContentResponse)
    utf8_response.candidates = [candidate]

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=utf8_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Call function
        result = await read_video(test_url, str(output_file))

        # Assertions
        assert result == utf8_content
        assert output_file.read_text(encoding="utf-8") == utf8_content


@pytest.mark.asyncio
async def test_read_video_uses_default_prompt(
    mock_config, mock_secret_manager, mock_gemini_response, temp_output_dir
):
    """Test that read_video uses the default prompt from YouTubeReader"""
    test_url = "https://youtube.com/watch?v=prompttest"
    output_file = temp_output_dir / "prompt_test.md"
    expected_prompt = "This is the default video analysis prompt"

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value=expected_prompt)
        mock_yt_instance.analyze_video = AsyncMock(return_value=mock_gemini_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Call function
        await read_video(test_url, str(output_file))

        # Verify the correct prompt was used
        mock_yt_instance.get_default_prompt.assert_called_once()
        mock_yt_instance.analyze_video.assert_called_once_with(test_url, expected_prompt)


@pytest.mark.asyncio
async def test_read_video_returns_content(
    mock_config, mock_secret_manager, mock_gemini_response, temp_output_dir
):
    """Test that read_video returns the analyzed content"""
    test_url = "https://youtube.com/watch?v=returntest"
    output_file = temp_output_dir / "return_test.md"

    with patch("ytreader.Config", return_value=mock_config), \
         patch("ytreader.SecretManager", return_value=mock_secret_manager), \
         patch("ytreader.YouTubeReader") as mock_yt_reader:

        # Setup mock YouTubeReader
        mock_yt_instance = Mock()
        mock_yt_instance.get_default_prompt = Mock(return_value="Summarize this video")
        mock_yt_instance.analyze_video = AsyncMock(return_value=mock_gemini_response)
        mock_yt_reader.return_value = mock_yt_instance

        # Call function
        result = await read_video(test_url, str(output_file))

        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "This is a test video summary about Python programming."
