from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class GoogleModel(str, Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"


class TimestampEntry(BaseModel):
    """Model for individual timestamp entries"""

    time: str = Field(..., description="Timestamp in format HH:MM or HH:MM:SS")
    description: str = Field(
        ..., description="Description of what happens at this timestamp"
    )


class VideoAnalysis(BaseModel):
    """Data structure for video analysis results"""

    url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(None, description="Video title")
    duration: Optional[str] = Field(None, description="Video duration")
    summary: str = Field(..., description="Comprehensive video summary")
    key_topics: list[str] = Field(
        default_factory=list, description="List of key topics discussed"
    )
    timestamps: list[TimestampEntry] = Field(
        default_factory=list, description="Key moments with timestamps"
    )
    sentiment: Optional[str] = Field(
        None, description="Overall sentiment of the content"
    )
    content_type: Optional[str] = Field(
        None, description="Classification of content type"
    )


class TokenDetails(BaseModel):
    modality: str
    tokenCount: int


class UsageMetadata(BaseModel):
    promptTokenCount: int
    candidatesTokenCount: int
    totalTokenCount: int
    promptTokensDetails: List[TokenDetails]
    thoughtsTokenCount: int


class ContentPart(BaseModel):
    text: str


class Content(BaseModel):
    parts: List[ContentPart]
    role: str


class Candidate(BaseModel):
    content: Content
    finishReason: str
    index: int


class GeminiYouTubeResponse(BaseModel):
    candidates: List[Candidate]
    usageMetadata: UsageMetadata
    modelVersion: str
    responseId: str
