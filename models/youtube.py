from config import Config
from secret_manager import SecretManager
from models.youtube_models import GeminiYouTubeResponse
from typing import List, Optional, Tuple, Union
import re
import requests
import httpx
import asyncio
from copy import deepcopy
from pathlib import Path


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
            self.config.gemini_api_key_path)
        self.base_url = self.config.gemini_base_url
        self.headers = self._build_headers()
        self.gemini_token_limit = 1048576
        self.max_tokens_per_chunk = int(
            self.gemini_token_limit * 0.9
        )  # 90% safety buffer

    def _build_headers(self) -> dict:
        """Build HTTP headers for Gemini API requests."""
        return {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

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
        if not hasattr(first_part, "text") or not first_part.text:
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
        data = {"contents": [
            {"parts": [{"file_data": {"file_uri": youtube_url}}]}]}

        url = f"{self.base_url}models/{self.model}:countTokens"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        result = response.json()

        return result["totalTokens"]

    async def estimate_token_rate(
        self, youtube_url: str, sample_duration: int = 60
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
            "contents": [
                {
                    "parts": [
                        {
                            "file_data": {"file_uri": youtube_url},
                            "video_metadata": {
                                "start_offset": "0s",
                                "end_offset": f"{sample_duration}s",
                            },
                        }
                    ]
                }
            ]
        }

        url = f"{self.base_url}models/{self.model}:countTokens"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, headers=self.headers, json=sample_data
                )
                response.raise_for_status()
                result = response.json()
                sample_tokens = result["totalTokens"]

            # Calculate tokens per second with 10% safety buffer for variation
            tokens_per_second = (sample_tokens / sample_duration) * 1.1

            return tokens_per_second

        except Exception as e:
            raise RuntimeError(f"Failed to estimate token rate: {str(e)}")

    def calculate_chunks(
        self, total_tokens: int, tokens_per_second: float, max_tokens: int = None
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

    def _get_default_prompt(
        self,
        filename: str = "youtube_prompt.md",
        encoding: str = "utf-8",
        directory: Optional[Union[str, Path]] = None
    ) -> str:
        """Get the default comprehensive analysis prompt."""
        if directory:
            file_path = Path(directory) / filename
        else:
            file_path = Path(filename)

        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding=encoding)
            return content

        else:
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
        self, youtube_url: str, prompt: str, url: str
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
            "contents": [
                {"parts": [{"text": prompt}, {
                    "file_data": {"file_uri": youtube_url}}]}
            ]
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            return GeminiYouTubeResponse(**response_data)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send msg to Gemini: {str(e)}")
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error when sending video: {str(e)}")

    async def _process_chunks_concurrent(
        self,
        youtube_url: str,
        prompt: str,
        url: str,
        chunk_boundaries: List[Tuple[int, int]],
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
                "contents": [
                    {
                        "parts": [
                            {
                                "file_data": {"file_uri": youtube_url},
                                "video_metadata": {
                                    "start_offset": f"{start}s",
                                    "end_offset": f"{end}s",
                                },
                            },
                            {"text": prompt},
                        ]
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, headers=self.headers, json=chunk_data)
                response.raise_for_status()
                return GeminiYouTubeResponse(**response.json())

        # Process all chunks concurrently
        tasks = [process_chunk(start, end) for start, end in chunk_boundaries]
        return await asyncio.gather(*tasks)

    def _combine_chunk_responses(
        self, responses: List[GeminiYouTubeResponse]
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
        combined_text = "\n\n".join(
            [
                f"--- Chunk {i+1} ({len(responses)} total chunks) ---\n{
                    r.candidates[0].content.parts[0].text}"
                for i, r in enumerate(responses)
            ]
        )

        combined.candidates[0].content.parts[0].text = combined_text

        return combined

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
            chunk_boundaries = self.calculate_chunks(
                token_count, tokens_per_second)

            # Process all chunks concurrently
            chunk_responses = await self._process_chunks_concurrent(
                youtube_url, prompt, url, chunk_boundaries
            )

            # Validate all responses
            for i, response in enumerate(chunk_responses):
                if not self.validate_response(response):
                    raise RuntimeError(
                        f"Invalid response structure from Gemini API for chunk {
                            i+1}"
                    )

            # Combine responses
            return self._combine_chunk_responses(chunk_responses)

        except Exception as e:
            raise RuntimeError(f"Failed to analyze chunked video: {str(e)}")
