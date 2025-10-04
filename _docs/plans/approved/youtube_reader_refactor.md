# Plan: Refactor YouTube Analysis to Dedicated YouTubeReader Class

## Overview
Extract all YouTube video analysis functionality from `GeminiMCP` into a dedicated `YouTubeReader` class in a new file `models/youtube.py`. This refactor will:
1. Create a clean separation of concerns (YouTube analysis vs general Gemini API operations)
2. Implement the intelligent video chunking system with token-to-seconds heuristic
3. Make the codebase more maintainable and testable
4. Remove YouTube-specific code from `GeminiMCP`

## Problem Analysis
Currently, `models/gemini_mcp.py` contains:
- General Gemini API operations (send_message, count_tokens, get_model_list)
- YouTube-specific video analysis (analyze_video, validate_youtube_url, count_tokens_video)

This mixing of concerns makes the class harder to maintain and test. YouTube analysis deserves its own dedicated class.

## Solution Approach

### Phase 1: Create YouTubeReader Class

**Location**: Create new file `models/youtube.py`

```python
from config import Config
from secret_manager import SecretManager
from models.youtube_models import VideoAnalysis, GeminiYouTubeResponse
from typing import List, Optional, Tuple
import re
import requests
import httpx
import asyncio
from copy import deepcopy


class YouTubeReader:
    """
    Dedicated class for YouTube video analysis using Gemini's multimodal API.

    This class handles all YouTube-specific operations including:
    - Video URL validation
    - Token counting for videos
    - Intelligent chunking for long videos
    - Concurrent processing of video chunks
    """

    def __init__(
        self,
        config: Config,
        secret_mgr: SecretManager,
        model: str = "gemini-2.5-flash",
    ) -> None:
        """
        Initialize YouTubeReader with configuration and credentials.

        Args:
            config: Configuration object with Gemini API settings
            secret_mgr: SecretManager instance for API key retrieval
            model: Gemini model name (default: gemini-2.5-flash)
        """
        self.config = config
        self.secret_mgr = secret_mgr
        self.model = model
        self.api_key = self.secret_mgr.get_secret(
            self.config.gemini_api_key_path
        )
        self.base_url = self.config.gemini_base_url
        self.headers = self._build_headers()
        self.gemini_token_limit = 1048576
        self.max_tokens_per_chunk = int(self.gemini_token_limit * 0.9)  # 90% safety buffer

    def _build_headers(self) -> dict:
        """Build HTTP headers for Gemini API requests."""
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def validate_youtube_url(self, url: str) -> bool:
        """
        Validate YouTube URL format.

        Args:
            url: URL string to validate

        Returns:
            True if valid YouTube URL, False otherwise
        """
        youtube_patterns = [
            r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]*)",
            r"(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]*)",
            r"(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]*)",
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)

    def validate_response(self, response: GeminiYouTubeResponse) -> bool:
        """
        Validate that the Gemini response has the expected structure.

        Args:
            response: GeminiYouTubeResponse object to validate

        Returns:
            bool: True if response is valid, False otherwise
        """
        if not response or not response.candidates:
            return False

        if len(response.candidates) == 0:
            return False

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            return False

        if len(candidate.content.parts) == 0:
            return False

        # Check if the first part has text
        first_part = candidate.content.parts[0]
        if not hasattr(first_part, 'text') or not first_part.text:
            return False

        return True

    async def count_tokens_video(self, youtube_url: str) -> int:
        """
        Count total tokens for entire video.

        Args:
            youtube_url: YouTube video URL

        Returns:
            Total token count for the video
        """
        data = {
            "contents": [
                {"parts": [
                    {"file_data": {"file_uri": youtube_url}}
                ]}
            ]
        }

        url = f"{self.base_url}models/{self.model}:countTokens"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        result = response.json()

        return result["totalTokens"]

    async def estimate_token_rate(
        self,
        youtube_url: str,
        sample_duration: int = 60
    ) -> float:
        """
        Estimate tokens per second by sampling the first N seconds of video.

        Args:
            youtube_url: YouTube video URL
            sample_duration: Seconds to sample (default 60s)

        Returns:
            Estimated tokens per second (float)
        """
        # Sample first 60 seconds
        sample_data = {
            "contents": [{
                "parts": [{
                    "file_data": {"file_uri": youtube_url},
                    "video_metadata": {
                        "start_offset": "0s",
                        "end_offset": f"{sample_duration}s"
                    }
                }]
            }]
        }

        url = f"{self.base_url}models/{self.model}:countTokens"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self.headers, json=sample_data)
                response.raise_for_status()
                result = response.json()
                sample_tokens = result["totalTokens"]

            # Calculate tokens per second with 10% safety buffer for variation
            tokens_per_second = (sample_tokens / sample_duration) * 1.1

            return tokens_per_second

        except Exception as e:
            raise RuntimeError(f"Failed to estimate token rate: {str(e)}")

    def calculate_chunks(
        self,
        total_tokens: int,
        tokens_per_second: float,
        max_tokens: int = None
    ) -> List[Tuple[int, int]]:
        """
        Calculate optimal chunk boundaries in seconds.

        Args:
            total_tokens: Total video tokens
            tokens_per_second: Estimated tokens/second rate
            max_tokens: Max tokens per chunk (default: 90% of limit for safety)

        Returns:
            List of (start_seconds, end_seconds) tuples
        """
        max_tokens = max_tokens or self.max_tokens_per_chunk

        # Calculate total video duration
        total_duration = int(total_tokens / tokens_per_second)

        # Calculate chunk duration based on token limit
        chunk_duration = int(max_tokens / tokens_per_second)

        # Generate chunk boundaries
        chunks = []
        start = 0

        while start < total_duration:
            end = min(start + chunk_duration, total_duration)
            chunks.append((start, end))
            start = end

        return chunks

    def _get_default_prompt(self) -> str:
        """Get the default comprehensive analysis prompt."""
        return """
        Please analyze this YouTube video comprehensively and provide:

        1. **Video Summary**: A detailed 3-4 paragraph summary of the main content
        2. **Key Topics**: List the 3-5 most important topics discussed
        3. **Timestamps**: Identify 5-7 key moments with timestamps and descriptions
        4. **Main Takeaways**: 3-5 key insights or actionable points
        5. **Key quotes from the speaker**: Identify critical quotes that are pertinent to the content presented.

        Focus on both visual and audio elements. Pay attention to:
        - Spoken content and dialogue
        - Visual elements, graphics, and text shown
        - Scene changes and transitions
        - Background music or sounds that add context

        Format your response in a structured markdown with clear sections.
        """

    async def _process_single_video(
        self,
        youtube_url: str,
        prompt: str,
        url: str
    ) -> GeminiYouTubeResponse:
        """
        Process video that fits within token limit (no chunking needed).

        Args:
            youtube_url: YouTube video URL
            prompt: Analysis prompt
            url: API endpoint URL

        Returns:
            GeminiYouTubeResponse
        """
        data = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"file_data": {"file_uri": youtube_url}}
                ]
            }]
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            return GeminiYouTubeResponse(**response_data)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send msg to Gemini: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error when sending video: {str(e)}")

    async def _process_chunks_concurrent(
        self,
        youtube_url: str,
        prompt: str,
        url: str,
        chunk_boundaries: List[Tuple[int, int]]
    ) -> List[GeminiYouTubeResponse]:
        """
        Process all chunks concurrently.

        Args:
            youtube_url: YouTube video URL
            prompt: Analysis prompt
            url: API endpoint URL
            chunk_boundaries: List of (start_seconds, end_seconds) tuples

        Returns:
            List of GeminiYouTubeResponse objects, one per chunk
        """
        async def process_chunk(start: int, end: int):
            chunk_data = {
                "contents": [{
                    "parts": [
                        {
                            "file_data": {"file_uri": youtube_url},
                            "video_metadata": {
                                "start_offset": f"{start}s",
                                "end_offset": f"{end}s"
                            }
                        },
                        {"text": prompt}
                    ]
                }]
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, headers=self.headers, json=chunk_data)
                response.raise_for_status()
                return GeminiYouTubeResponse(**response.json())

        # Process all chunks concurrently
        tasks = [process_chunk(start, end) for start, end in chunk_boundaries]
        return await asyncio.gather(*tasks)

    def _combine_chunk_responses(
        self,
        responses: List[GeminiYouTubeResponse]
    ) -> GeminiYouTubeResponse:
        """
        Combine multiple chunk responses into single response.

        Args:
            responses: List of GeminiYouTubeResponse objects from chunks

        Returns:
            Single combined GeminiYouTubeResponse
        """
        # Use first response as template
        combined = deepcopy(responses[0])

        # Concatenate all text parts with chunk markers
        combined_text = "\n\n".join([
            f"--- Chunk {i+1} ({len(responses)} total chunks) ---\n{r.candidates[0].content.parts[0].text}"
            for i, r in enumerate(responses)
        ])

        combined.candidates[0].content.parts[0].text = combined_text

        return combined

    async def analyze_video(
        self,
        youtube_url: str,
        prompt: Optional[str] = None
    ) -> GeminiYouTubeResponse:
        """
        Analyze YouTube video using Gemini's multimodal capabilities.
        Automatically chunks videos that exceed token limits.

        Args:
            youtube_url: Valid YouTube video URL
            prompt: Optional custom analysis prompt

        Returns:
            GeminiYouTubeResponse object with comprehensive results

        Raises:
            ValueError: If YouTube URL is invalid
            RuntimeError: If API request fails or response is invalid
        """
        if not self.validate_youtube_url(youtube_url):
            raise ValueError(f"Invalid YouTube URL provided: {youtube_url}")

        prompt = prompt or self._get_default_prompt()
        url = f"{self.base_url}models/{self.model}:generateContent"

        # Get total token count
        token_count = await self.count_tokens_video(youtube_url)

        # If under limit, process normally
        if token_count < self.gemini_token_limit:
            return await self._process_single_video(youtube_url, prompt, url)

        # Video exceeds limit - use dynamic chunking
        try:
            # Estimate token rate from sample
            tokens_per_second = await self.estimate_token_rate(youtube_url)

            # Calculate optimal chunks
            chunk_boundaries = self.calculate_chunks(token_count, tokens_per_second)

            # Process all chunks concurrently
            chunk_responses = await self._process_chunks_concurrent(
                youtube_url, prompt, url, chunk_boundaries
            )

            # Validate all responses
            for i, response in enumerate(chunk_responses):
                if not self.validate_response(response):
                    raise RuntimeError(
                        f"Invalid response structure from Gemini API for chunk {i+1}"
                    )

            # Combine responses
            return self._combine_chunk_responses(chunk_responses)

        except Exception as e:
            raise RuntimeError(f"Failed to analyze chunked video: {str(e)}")
```

### Phase 2: Remove YouTube Functionality from GeminiMCP

**Location**: `models/gemini_mcp.py`

#### Methods to Remove:
1. Line 126-133: `validate_youtube_url()`
2. Line 135-163: `validate_response()`
3. Line 165-300: `analyze_video()`
4. Line 302-316: `_parse_analysis_response()`
5. Line 318-335: `count_tokens_video()`

#### Import to Remove:
- Line 8: `from models.youtube_models import VideoAnalysis, GeminiYouTubeResponse`

### Phase 3: Update Imports and Tests

#### Update `models/test_gemini_mcp.py`

**Remove YouTube tests**:
```python
# Lines to remove or move to new test file:
@pytest.mark.asyncio
async def test_youtube(gemini_mcp):
    # Move to test_youtube.py

@pytest.mark.asyncio
async def test_count_tokens_video(gemini_mcp):
    # Move to test_youtube.py
```

#### Create `models/test_youtube.py`

```python
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
    assert youtube_reader.validate_youtube_url(
        "https://youtu.be/dQw4w9WgXcQ"
    )
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

    print(f"Chunked analysis result: {result.candidates[0].content.parts[0].text[:500]}...")


@pytest.mark.asyncio
async def test_custom_prompt(youtube_reader):
    """Test video analysis with custom prompt"""
    yt_url = "https://www.youtube.com/watch?v=6stlCkUDG_s"
    custom_prompt = "List the main technical concepts discussed in this video"

    result = await youtube_reader.analyze_video(yt_url, prompt=custom_prompt)

    assert result is not None
    print(f"Custom prompt result: {result.candidates[0].content.parts[0].text}")
```

### Phase 4: Update Exports and Documentation

#### Update `models/__init__.py`

```python
# Add to existing imports
from models.youtube import YouTubeReader

__all__ = [
    # ... existing exports ...
    "YouTubeReader",
]
```

#### Update `CLAUDE.md`

Add to architecture section:
```markdown
### Models Package
The `models/` directory contains unified API wrappers for different AI providers:
- **anthropic_mpc.py**: Anthropic Claude API integration
- **openai_mpc.py**: OpenAI API integration
- **gemini_mcp.py**: Google Gemini API integration (general text operations)
- **xai_mcp.py**: XAI/Grok API integration
- **youtube.py**: YouTube video analysis using Gemini multimodal API
```

## Implementation Steps

### Step 1: Create YouTubeReader Class
- Create `models/youtube.py` with complete YouTubeReader implementation
- Include all helper methods and main analyze_video() method
- Add comprehensive docstrings

### Step 2: Create Test File
- Create `models/test_youtube.py` with all test cases
- Move existing YouTube tests from test_gemini_mcp.py
- Add new tests for chunking functionality

### Step 3: Remove YouTube Code from GeminiMCP
- Remove methods: validate_youtube_url, validate_response, analyze_video, _parse_analysis_response, count_tokens_video
- Remove import: `from models.youtube_models import VideoAnalysis, GeminiYouTubeResponse`
- Clean up any YouTube-related comments

### Step 4: Update Module Exports
- Add YouTubeReader to `models/__init__.py`
- Update documentation in CLAUDE.md

### Step 5: Run Tests
```bash
# Test new YouTubeReader class
uv run pytest models/test_youtube.py -v -s

# Verify GeminiMCP still works
uv run pytest models/test_gemini_mcp.py -v -s

# Run all model tests
uv run pytest models/ -v -n auto
```

## Files to Create

1. **`models/youtube.py`** - New YouTubeReader class (400+ lines)
2. **`models/test_youtube.py`** - Comprehensive test suite (150+ lines)

## Files to Modify

1. **`models/gemini_mcp.py`**:
   - Remove lines 8, 126-335 (YouTube-related code)
   - Keep general Gemini API methods

2. **`models/test_gemini_mcp.py`**:
   - Remove or comment out YouTube-specific tests
   - Keep general Gemini API tests

3. **`models/__init__.py`**:
   - Add YouTubeReader export

4. **`CLAUDE.md`**:
   - Update architecture documentation

## Key Benefits

1. **Separation of Concerns**: YouTube analysis isolated from general Gemini operations
2. **Improved Maintainability**: Easier to update YouTube-specific logic
3. **Better Testing**: Dedicated test suite for YouTube functionality
4. **Clear API**: YouTubeReader provides focused interface for video analysis
5. **Enhanced Chunking**: Implements intelligent token-based chunking system
6. **Backward Compatibility**: Can maintain GeminiMCP interface if needed via composition

## Testing Considerations

- Test URL validation with various YouTube formats
- Verify token counting accuracy
- Test chunking logic with different video lengths
- Validate concurrent chunk processing
- Test error handling for invalid URLs/responses
- Verify combined responses maintain proper structure

## Example Usage After Refactor

```python
# Old way (in GeminiMCP)
gemini_mcp = GeminiMCP(config, secret_mgr, "gemini-2.5-flash")
result = await gemini_mcp.analyze_video(youtube_url)

# New way (dedicated YouTubeReader)
youtube_reader = YouTubeReader(config, secret_mgr, "gemini-2.5-flash")
result = await youtube_reader.analyze_video(youtube_url)

# Automatic chunking for long videos
long_result = await youtube_reader.analyze_video(long_youtube_url)

# Custom prompt
custom_result = await youtube_reader.analyze_video(
    youtube_url,
    prompt="Summarize technical concepts"
)
```

## Migration Path

For backward compatibility (if needed), `GeminiMCP` can delegate to `YouTubeReader`:

```python
# In gemini_mcp.py (optional compatibility layer)
from models.youtube import YouTubeReader

class GeminiMCP:
    def __init__(self, config, secret_mgr, model):
        # ... existing init ...
        self._youtube_reader = YouTubeReader(config, secret_mgr, model)

    async def analyze_video(self, youtube_url: str, prompt: str = None):
        """Deprecated: Use YouTubeReader directly"""
        return await self._youtube_reader.analyze_video(youtube_url, prompt)
```

## Future Enhancements

1. **Multi-Provider Support**: Abstract interface for other video analysis APIs
2. **Caching Layer**: Cache token estimates for similar videos
3. **Progress Tracking**: Add callbacks for chunk processing progress
4. **Metadata Extraction**: Integrate YouTube Data API for video metadata
5. **Smart Summarization**: Use LLM to merge chunk analyses intelligently
