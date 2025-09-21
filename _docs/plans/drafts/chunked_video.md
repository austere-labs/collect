# Plan: Add Chunked Video Analysis for Long YouTube Videos

## Overview
Implement functionality to analyze YouTube videos that exceed Gemini's 1,048,576 token limit by splitting them into 2 chunks and analyzing each chunk separately. This will allow processing of longer videos that would otherwise fail due to token count restrictions.

## Implementation Steps

### 1. Add chunked video analysis method
Add a new method `analyze_video_chunked` to the `GeminiMCP` class in `models/gemini_mcp.py`:

```python
async def analyze_video_chunked(self, youtube_url: str, prompt: str = None) -> list:
    """
    Analyze a long video by splitting it into 2 chunks
    Returns a list of 2 VideoAnalysis results
    """
    # First check if video exceeds token limit
    try:
        total_tokens = await self.count_tokens_video(youtube_url)
        if total_tokens <= self.gemini_token_limit:
            # Video is small enough, analyze normally
            return [await self.analyze_video(youtube_url, prompt)]
    except Exception as e:
        print(f"Could not check token count, proceeding with chunking: {e}")
    
    # Split into 2 chunks by creating URLs with time parameters
    # Chunk 1: Start from beginning (no time parameter needed)
    chunk1_url = youtube_url
    
    # Chunk 2: Start from middle (add time parameter)
    # YouTube URLs support &t=XXXs format for start time
    separator = "&" if "?" in youtube_url else "?"
    # Estimate middle point - this is approximate since we don't know video duration
    # For better accuracy, you could use YouTube API to get actual video duration
    chunk2_url = f"{youtube_url}{separator}t=50%"  # Start from 50% through video
    
    results = []
    
    # Analyze first chunk
    try:
        chunk1_result = await self.analyze_video(chunk1_url, prompt)
        results.append(chunk1_result)
    except Exception as e:
        print(f"Failed to analyze first chunk: {e}")
    
    # Analyze second chunk  
    try:
        chunk2_result = await self.analyze_video(chunk2_url, prompt)
        results.append(chunk2_result)
    except Exception as e:
        print(f"Failed to analyze second chunk: {e}")
        
    return results
```

### 2. Add error handling improvements
Enhance the `analyze_video` method to provide better error messages when token limits are exceeded, suggesting the use of chunked analysis.

### 3. Add test case for chunked analysis
Create a test in `models/test_gemini_mcp.py` to verify the chunked analysis functionality:

```python
@pytest.mark.asyncio
async def test_youtube_chunked(gemini_mcp):
    # Test with a long video that exceeds token limits
    long_video_url = "https://www.youtube.com/watch?v=_IlTcWciEC4"  # Known long video
    results = await gemini_mcp.analyze_video_chunked(long_video_url)
    
    assert isinstance(results, list)
    assert len(results) <= 2  # Should return 1-2 results
    
    for result in results:
        print(f"Chunk result: {result}")
```

### 4. Update documentation
Add usage examples and documentation for the new chunked analysis feature.

## Key Features
- **Automatic token limit detection**: Check if video exceeds limits before processing
- **Fallback to normal analysis**: Use regular analysis for shorter videos  
- **Two-chunk splitting**: Split long videos into 2 approximately equal parts
- **Error resilience**: Continue processing even if one chunk fails
- **Flexible prompting**: Support custom prompts for each chunk

## Testing Considerations
- Test with videos of various lengths (short, medium, long)
- Verify proper URL formatting with time parameters
- Test error handling when chunks fail
- Validate that short videos still use normal analysis path
- Test with different YouTube URL formats (youtube.com, youtu.be, etc.)

## Example Usage

```python
# For a long video that exceeds token limits
gemini_mcp = GeminiMCP(config, secret_mgr, "gemini-2.5-flash")

# This will automatically chunk if needed
results = await gemini_mcp.analyze_video_chunked("https://www.youtube.com/watch?v=long-video-id")

# Results will be a list of 1-2 VideoAnalysis objects
for i, result in enumerate(results):
    print(f"Chunk {i+1}: {result.summary}")
```

## Limitations
- Video splitting uses estimated 50% midpoint (not exact video duration)
- YouTube's time parameter support may vary by video
- Some context may be lost between chunks
- No automatic merging of chunk results into single analysis

## Future Enhancements
- Integrate YouTube API to get exact video duration for precise splitting
- Add configurable chunk count (not just 2)
- Implement result merging to combine chunk analyses
- Add overlap between chunks to maintain context continuity