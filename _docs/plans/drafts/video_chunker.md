# Plan: Build Token-to-Seconds Heuristic for Intelligent Video Chunking

## Overview
Currently, the `analyze_video()` method hardcodes 30-minute (1800s) chunks when videos exceed the token limit. For a 2.5-hour video, this approach would need multiple sequential chunk pairs. This plan implements a dynamic system that:
1. Estimates tokens-per-second for a video
2. Calculates optimal chunk sizes based on token limit
3. Processes all chunks concurrently

## Problem Analysis
The current implementation in `models/gemini_mcp.py:204-275` splits videos into exactly two chunks (0-1800s and 1800s-end) when the token count exceeds `self.gemini_token_limit` (1,048,576). This approach has limitations:
- Fixed 30-minute chunks don't adapt to video content density
- Only handles 2 chunks, insufficient for very long videos
- Sequential processing of chunks is inefficient

## Solution Approach

### 1. Sample-Based Token Estimation
**Location**: `models/gemini_mcp.py` - Add new method after `count_tokens_video()` (around line 336)

```python
async def estimate_token_rate(self, youtube_url: str, sample_duration: int = 60) -> float:
    """
    Estimate tokens per second by sampling the first N seconds of video.

    Args:
        youtube_url: YouTube video URL
        sample_duration: Seconds to sample (default 60s)

    Returns:
        Estimated tokens per second (float)
    """
    import httpx

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
```

### 2. Dynamic Chunk Calculator
**Location**: `models/gemini_mcp.py` - Add new method after `estimate_token_rate()`

```python
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
    max_tokens = max_tokens or int(self.gemini_token_limit * 0.9)

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
```

### 3. Concurrent Chunk Processing Helper
**Location**: `models/gemini_mcp.py` - Add new method after `calculate_chunks()`

```python
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
    import asyncio
    import httpx

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
```

### 4. Response Combiner Helper
**Location**: `models/gemini_mcp.py` - Add new method after `_process_chunks_concurrent()`

```python
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
    from copy import deepcopy

    # Use first response as template
    combined = deepcopy(responses[0])

    # Concatenate all text parts with chunk markers
    combined_text = "\n\n".join([
        f"--- Chunk {i+1} ({len(responses)} total chunks) ---\n{r.candidates[0].content.parts[0].text}"
        for i, r in enumerate(responses)
    ])

    combined.candidates[0].content.parts[0].text = combined_text

    return combined
```

### 5. Single Video Processing Helper
**Location**: `models/gemini_mcp.py` - Extract existing code into new method

```python
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
        import requests
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return GeminiYouTubeResponse(**response_data)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to send msg to Gemini: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error when sending video: {str(e)}")
```

### 6. Default Prompt Helper
**Location**: `models/gemini_mcp.py` - Extract default prompt to method

```python
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
```

### 7. Refactor analyze_video() Method
**Location**: `models/gemini_mcp.py:165-300` - Replace existing implementation

```python
async def analyze_video(
    self, youtube_url: str, prompt: Optional[str] = None
) -> GeminiYouTubeResponse:
    """
    Analyze YouTube video using Gemini's multimodal capabilities.
    Automatically chunks videos that exceed token limits.

    Args:
        youtube_url: Valid YouTube video URL
        prompt: Optional custom analysis prompt

    Returns:
        GeminiYouTubeResponse object with comprehensive results
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

## Implementation Steps

### Step 1: Add Helper Methods
Add the following methods to `GeminiMCP` class in order:
1. `_get_default_prompt()` - Extract default prompt (line ~370)
2. `estimate_token_rate()` - Token estimation via sampling (line ~375)
3. `calculate_chunks()` - Dynamic chunk calculator (line ~410)
4. `_process_single_video()` - Single video processor (line ~445)
5. `_process_chunks_concurrent()` - Concurrent chunk processor (line ~475)
6. `_combine_chunk_responses()` - Response combiner (line ~515)

### Step 2: Refactor analyze_video()
Replace lines 165-300 with new implementation that:
- Validates URL
- Gets token count
- Routes to single or chunked processing
- Returns combined result

### Step 3: Add Type Hints
Add to imports at top of file:
```python
from typing import Dict, List, Optional, Tuple  # Add Tuple
```

### Step 4: Update Tests
Add test in `models/test_gemini_mcp.py`:

```python
@pytest.mark.asyncio
async def test_analyze_long_video_chunking(gemini_mcp):
    """Test dynamic chunking for videos exceeding token limit"""
    # Use a known long video (>2 hours)
    long_video_url = "https://www.youtube.com/watch?v=LONG_VIDEO_ID"

    result = await gemini_mcp.analyze_video(long_video_url)

    # Should succeed with chunked processing
    assert result is not None
    assert result.candidates[0].content.parts[0].text
    assert "Chunk" in result.candidates[0].content.parts[0].text

    print(f"Long video analysis result: {result.candidates[0].content.parts[0].text[:500]}...")
```

## Key Benefits

1. **Dynamic Adaptation**: Chunk size adapts to video content density
2. **Accurate Estimation**: Sample-based approach provides real token rates
3. **Concurrent Processing**: All chunks processed in parallel for speed
4. **Handles Any Length**: Works for 30min, 2.5hrs, or longer videos
5. **Safety Buffers**:
   - Uses 90% of token limit for chunks
   - Adds 10% buffer to token rate estimation
6. **Backward Compatible**: Single videos continue to work as before

## Testing Considerations

- Test with videos of various lengths (5min, 30min, 1hr, 2.5hr, 4hr)
- Verify token estimation accuracy across different content types
- Test concurrent chunk processing doesn't hit rate limits
- Validate combined response structure matches expected format
- Test error handling when sampling fails
- Verify chunk boundary calculations are correct

## Example Usage

```python
# Initialize
gemini_mcp = GeminiMCP(config, secret_mgr, "gemini-2.5-flash")

# Short video (< 1M tokens) - processes normally
result = await gemini_mcp.analyze_video("https://www.youtube.com/watch?v=SHORT_VIDEO")

# Long video (2.5 hours) - automatically chunks
result = await gemini_mcp.analyze_video("https://www.youtube.com/watch?v=LONG_VIDEO")

# Custom prompt with chunking
custom_prompt = "Summarize the key technical concepts discussed"
result = await gemini_mcp.analyze_video(long_url, prompt=custom_prompt)

# Result contains combined analysis from all chunks
print(result.candidates[0].content.parts[0].text)
```

## Files Modified

- **`models/gemini_mcp.py`**:
  - Line 165-300: Refactor `analyze_video()`
  - Line 370-540: Add new helper methods
  - Line 7: Update imports to include `Tuple`

## Future Enhancements

1. **Adaptive Sampling**: Use multiple samples from different parts of video for better estimation
2. **Chunk Overlap**: Add configurable overlap between chunks for context continuity
3. **Smart Merging**: Use LLM to intelligently merge chunk analyses into coherent summary
4. **Caching**: Cache token rate estimates for similar video types
5. **Progress Callbacks**: Add callback support for chunk processing progress
6. **Metadata Integration**: Use YouTube API to get exact duration instead of estimating
