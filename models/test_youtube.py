import pytest
from config import Config
from secret_manager import SecretManager
from models.youtube import YouTubeReader


@pytest.fixture
def youtube_reader():
    """Fixture to create YouTubeReader instance"""
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    return YouTubeReader(config, secret_mgr, "gemini-2.5-flash")


@pytest.mark.asyncio
async def test_validate_youtube_url(youtube_reader):
    """Test YouTube URL validation"""
    assert youtube_reader.validate_youtube_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert youtube_reader.validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert not youtube_reader.validate_youtube_url("https://example.com")


@pytest.mark.asyncio
async def test_count_tokens_video(youtube_reader):
    """Test token counting for YouTube videos"""
    yt_url = "https://www.youtube.com/watch?v=6stlCkUDG_s"
    count = await youtube_reader.count_tokens_video(yt_url)

    assert count > 0
    print(f"Token count: {count}")


@pytest.mark.asyncio
async def test_estimate_token_rate(youtube_reader):
    """Test token rate estimation from video sample"""
    yt_url = "https://www.youtube.com/watch?v=6stlCkUDG_s"

    token_rate = await youtube_reader.estimate_token_rate(yt_url, sample_duration=30)

    assert token_rate > 0
    print(f"Estimated tokens per second: {token_rate}")


@pytest.mark.asyncio
async def test_calculate_chunks(youtube_reader):
    """Test chunk boundary calculation"""
    total_tokens = 1500000  # 1.5M tokens (exceeds limit)
    tokens_per_second = 500.0

    chunks = youtube_reader.calculate_chunks(total_tokens, tokens_per_second)

    assert len(chunks) > 1  # Should create multiple chunks
    assert all(isinstance(chunk, tuple) and len(chunk) == 2 for chunk in chunks)

    print(f"Created {len(chunks)} chunks: {chunks}")


@pytest.mark.asyncio
async def test_analyze_short_video(youtube_reader):
    """Test analysis of short video (no chunking needed)"""
    # Short video under token limit
    yt_url = "https://www.youtube.com/watch?v=6stlCkUDG_s"

    result = await youtube_reader.analyze_video(yt_url)

    assert result is not None
    assert result.candidates[0].content.parts[0].text
    print(f"Analysis result: {result.candidates[0].content.parts[0].text[:200]}...")


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow test
async def test_analyze_long_video_with_chunking(youtube_reader):
    """Test analysis of long video requiring chunking"""
    # Long video that exceeds token limit
    long_video_url = "https://www.youtube.com/watch?v=LONG_VIDEO_ID"

    result = await youtube_reader.analyze_video(long_video_url)

    assert result is not None
    assert result.candidates[0].content.parts[0].text
    assert "Chunk" in result.candidates[0].content.parts[0].text

    print(
        f"Chunked analysis result: {result.candidates[0].content.parts[0].text[:500]}..."
    )


@pytest.mark.asyncio
async def test_custom_prompt(youtube_reader):
    """Test video analysis with custom prompt"""
    yt_url = "https://www.youtube.com/watch?v=6stlCkUDG_s"
    custom_prompt = "List the main technical concepts discussed in this video"

    result = await youtube_reader.analyze_video(yt_url, prompt=custom_prompt)

    assert result is not None
    print(f"Custom prompt result: {result.candidates[0].content.parts[0].text}")
