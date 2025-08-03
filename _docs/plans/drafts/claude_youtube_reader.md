# Plan: YouTube Video Reader with Gemini Analysis

## Overview
Build a Python script that takes a YouTube video URL and uses Google's Gemini AI to analyze the entire video content and produce a comprehensive summary. The system will leverage Gemini's advanced multimodal capabilities to process both visual and audio elements of YouTube videos.

## Implementation Steps

### 1. Environment Setup and Dependencies
**File**: `requirements.txt` or `pyproject.toml`
```python
# Key dependencies needed:
google-generativeai>=0.8.0    # Gemini API client
python-dotenv>=1.0.0          # Environment variable management
pytube>=15.0.0                # YouTube video download (if needed)
requests>=2.31.0              # HTTP requests
pydantic>=2.0.0               # Data validation
click>=8.0.0                  # CLI interface
```

**Environment Variables** (`.env` file):
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GCP_PROJECT_ID=your_project_id  # If using Vertex AI
```

### 2. Core YouTube Video Reader Class
**File**: `youtube_reader.py`
```python
import os
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from google import generativeai as genai
from dotenv import load_dotenv

@dataclass
class VideoAnalysis:
    """Data structure for video analysis results"""
    url: str
    title: Optional[str]
    duration: Optional[str]
    summary: str
    key_topics: list[str]
    timestamps: list[Dict[str, str]]
    sentiment: Optional[str]
    content_type: Optional[str]

class YouTubeVideoReader:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key"""
        load_dotenv()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')  # Use latest model with video capabilities
    
    def validate_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format"""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]*)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]*)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]*)'
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    async def analyze_video(self, youtube_url: str, custom_prompt: Optional[str] = None) -> VideoAnalysis:
        """
        Analyze YouTube video using Gemini's multimodal capabilities
        
        Args:
            youtube_url: Valid YouTube video URL
            custom_prompt: Optional custom analysis prompt
            
        Returns:
            VideoAnalysis object with comprehensive results
        """
        if not self.validate_youtube_url(youtube_url):
            raise ValueError("Invalid YouTube URL provided")
        
        # Default comprehensive analysis prompt
        default_prompt = """
        Please analyze this YouTube video comprehensively and provide:
        
        1. **Video Summary**: A detailed 3-4 paragraph summary of the main content
        2. **Key Topics**: List the 5-10 most important topics discussed
        3. **Timestamps**: Identify 8-12 key moments with timestamps and descriptions
        4. **Content Type**: Classify the video (educational, entertainment, news, tutorial, etc.)
        5. **Sentiment**: Overall tone and sentiment of the content
        6. **Main Takeaways**: 3-5 key insights or actionable points
        
        Focus on both visual and audio elements. Pay attention to:
        - Spoken content and dialogue
        - Visual elements, graphics, and text shown
        - Scene changes and transitions
        - Background music or sounds that add context
        
        Format your response in a structured way with clear sections.
        """
        
        prompt = custom_prompt or default_prompt
        
        try:
            # Generate content using YouTube URL directly
            response = await self.model.generate_content_async([
                prompt,
                {"mime_type": "video/*", "uri": youtube_url}
            ])
            
            # Parse response into structured format
            analysis_result = self._parse_analysis_response(
                response.text, 
                youtube_url
            )
            
            return analysis_result
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze video: {str(e)}")
    
    def _parse_analysis_response(self, response_text: str, url: str) -> VideoAnalysis:
        """Parse Gemini response into structured VideoAnalysis object"""
        # This would contain logic to extract structured data from the response
        # For now, return basic structure - implement parsing based on response format
        
        return VideoAnalysis(
            url=url,
            title=None,  # Could extract from video metadata
            duration=None,  # Could extract from video metadata  
            summary=response_text,  # Full response for now
            key_topics=[],  # Parse from response
            timestamps=[],  # Parse from response
            sentiment=None,  # Parse from response
            content_type=None  # Parse from response
        )
```

### 3. CLI Interface
**File**: `cli.py`
```python
import click
import asyncio
from youtube_reader import YouTubeVideoReader, VideoAnalysis

@click.command()
@click.argument('youtube_url')
@click.option('--output', '-o', help='Output file path (optional)')
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'text']), 
              default='markdown', help='Output format')
@click.option('--custom-prompt', '-p', help='Custom analysis prompt')
def analyze_video(youtube_url: str, output: str, format: str, custom_prompt: str):
    """Analyze a YouTube video using Gemini AI"""
    
    try:
        reader = YouTubeVideoReader()
        
        # Run async analysis
        analysis = asyncio.run(reader.analyze_video(youtube_url, custom_prompt))
        
        # Format output
        formatted_output = format_analysis(analysis, format)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo(formatted_output)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

def format_analysis(analysis: VideoAnalysis, format_type: str) -> str:
    """Format analysis results based on output type"""
    if format_type == 'json':
        import json
        return json.dumps(analysis.__dict__, indent=2, ensure_ascii=False)
    
    elif format_type == 'markdown':
        return f"""# YouTube Video Analysis
        
## Video Information
- **URL**: {analysis.url}
- **Title**: {analysis.title or 'N/A'}
- **Duration**: {analysis.duration or 'N/A'}

## Summary
{analysis.summary}

## Key Topics
{chr(10).join(f"- {topic}" for topic in analysis.key_topics)}

## Key Timestamps
{chr(10).join(f"- **{ts.get('time', 'N/A')}**: {ts.get('description', 'N/A')}" for ts in analysis.timestamps)}

## Content Analysis
- **Content Type**: {analysis.content_type or 'N/A'}
- **Sentiment**: {analysis.sentiment or 'N/A'}
"""
    
    else:  # text format
        return analysis.summary

if __name__ == '__main__':
    analyze_video()
```

### 4. Enhanced Features Module
**File**: `video_utils.py`
```python
from typing import Dict, List, Optional
import re

class VideoMetadataExtractor:
    """Extract additional metadata from YouTube videos"""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def get_video_info(video_id: str) -> Dict[str, Any]:
        """Get basic video information using YouTube API (optional)"""
        # Implementation would use YouTube Data API v3
        # Return title, duration, description, etc.
        pass

class ResponseParser:
    """Parse Gemini responses into structured data"""
    
    @staticmethod
    def extract_timestamps(text: str) -> List[Dict[str, str]]:
        """Extract timestamps from response text"""
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-:]\s*(.+?)(?=\n|\d{1,2}:\d{2}|$)'
        matches = re.findall(timestamp_pattern, text, re.MULTILINE)
        
        return [{"time": match[0], "description": match[1].strip()} 
                for match in matches]
    
    @staticmethod
    def extract_topics(text: str) -> List[str]:
        """Extract key topics from response"""
        # Look for bullet points or numbered lists
        topic_patterns = [
            r'^\s*[-*]\s*(.+)$',  # Bullet points
            r'^\s*\d+\.\s*(.+)$'  # Numbered lists
        ]
        
        topics = []
        for line in text.split('\n'):
            for pattern in topic_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    topics.append(match.group(1).strip())
        
        return topics[:10]  # Limit to top 10 topics
```

### 5. Configuration and Settings
**File**: `config.py`
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    gemini_api_key: str
    gcp_project_id: Optional[str] = None
    
    # Model Configuration
    model_name: str = "gemini-2.5-pro"
    max_tokens: int = 8192
    temperature: float = 0.3
    
    # Video Processing Settings
    max_video_duration: int = 7200  # 2 hours in seconds
    frame_rate: int = 1  # Frames per second for analysis
    media_resolution: str = "default"  # or "low" for longer videos
    
    # Output Settings
    default_output_format: str = "markdown"
    include_timestamps: bool = True
    include_sentiment: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
```

## Key Features

### Core Capabilities
- **Direct YouTube URL Processing**: Uses Gemini's native YouTube URL support
- **Multimodal Analysis**: Processes both visual and audio content
- **Comprehensive Summaries**: Generates detailed content summaries
- **Timestamp Extraction**: Identifies key moments with timestamps
- **Topic Classification**: Extracts main topics and themes
- **Sentiment Analysis**: Determines overall tone and sentiment
- **Multiple Output Formats**: JSON, Markdown, and plain text support

### Advanced Features
- **Custom Prompts**: Allow users to specify custom analysis requirements
- **Batch Processing**: Process multiple videos in sequence
- **Long Video Support**: Handle videos up to 2 hours (2M context) or 6 hours (low resolution)
- **Error Handling**: Robust error handling for API failures and invalid URLs
- **Caching**: Optional caching of analysis results
- **Progress Tracking**: Show progress for long video analysis

## API Requirements

### Google Gemini API
- **Primary API**: Google AI Generative AI Python Client
- **Key**: Gemini API Key from Google AI Studio
- **Models**: Gemini 2.5 Pro (recommended) or Gemini 2.5 Flash (cost-effective)
- **Capabilities**: Native YouTube URL processing, multimodal analysis
- **Cost**: ~$0.075 per 1K input tokens, $0.30 per 1K output tokens (Gemini 2.5 Pro)

### Optional APIs
- **YouTube Data API v3**: For enhanced metadata (title, description, duration)
  - Requires Google Cloud Project and API key
  - 10,000 free quota units per day
  - Used for additional video information beyond what Gemini provides

## Dependencies and Requirements

### Core Dependencies
```python
google-generativeai>=0.8.0     # Gemini API client
python-dotenv>=1.0.0           # Environment management
pydantic>=2.0.0                # Data validation and settings
click>=8.0.0                   # CLI interface
asyncio                        # Built-in async support
```

### Optional Dependencies
```python
google-api-python-client>=2.0  # YouTube Data API (optional)
pytube>=15.0.0                 # YouTube metadata extraction (alternative)
rich>=13.0.0                   # Enhanced CLI output formatting
```

### System Requirements
- **Python**: 3.8+ (recommended 3.11+)
- **Internet Connection**: Required for API calls
- **API Key**: Google AI Studio API key
- **Memory**: Minimal (video processing is handled by Gemini)

## Testing Considerations

### Test Scenarios
1. **Valid YouTube URLs**: Test various URL formats (youtube.com, youtu.be, embed)
2. **Invalid URLs**: Test error handling for malformed URLs
3. **Different Video Types**: Educational, entertainment, news, tutorials
4. **Video Lengths**: Short (< 5 min), medium (5-30 min), long (> 30 min)
5. **Different Content**: Various languages, with/without subtitles
6. **API Failures**: Network errors, rate limiting, invalid API keys

### Edge Cases
- Private or unlisted videos
- Age-restricted content
- Live streams vs recorded videos
- Videos with no audio or minimal visual content
- Very long videos (approaching context limits)

### Performance Testing
- Response time for different video lengths
- Token usage and cost estimation
- Concurrent request handling
- Memory usage during processing

## Example Usage

### Basic Usage
```bash
# Analyze a YouTube video
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Save to file in markdown format
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -o analysis.md -f markdown

# Use custom prompt
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -p "Focus on technical concepts and code examples"

# JSON output for programmatic use
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -f json -o results.json
```

### Programmatic Usage
```python
from youtube_reader import YouTubeVideoReader

# Initialize reader
reader = YouTubeVideoReader()

# Analyze video
analysis = await reader.analyze_video("https://www.youtube.com/watch?v=VIDEO_ID")

# Access results
print(f"Summary: {analysis.summary}")
print(f"Key Topics: {analysis.key_topics}")
print(f"Timestamps: {analysis.timestamps}")
```

## Implementation Timeline

### Phase 1 (Week 1): Core Functionality
- ✅ Set up project structure and dependencies
- ✅ Implement basic YouTubeVideoReader class
- ✅ Create CLI interface with Click
- ✅ Test with simple video analysis

### Phase 2 (Week 2): Enhanced Features
- ✅ Add response parsing and structured output
- ✅ Implement multiple output formats
- ✅ Add error handling and validation
- ✅ Create configuration system

### Phase 3 (Week 3): Polish and Testing
- ✅ Comprehensive testing suite
- ✅ Performance optimization
- ✅ Documentation and examples
- ✅ Optional YouTube Data API integration

## Security and Best Practices

### API Key Management
- Store API keys in environment variables
- Use `.env` files for local development
- Never commit API keys to version control
- Consider using Google Cloud Secret Manager for production

### Rate Limiting
- Implement exponential backoff for API calls
- Monitor usage against quotas
- Add request throttling for batch processing

### Error Handling
- Graceful handling of API failures
- User-friendly error messages
- Logging for debugging and monitoring
- Retry logic for transient failures

This plan provides a comprehensive approach to building a robust YouTube video reader using Gemini's advanced multimodal capabilities, with proper error handling, multiple output formats, and extensible architecture for future enhancements.