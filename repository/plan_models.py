from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List


class PlanStatus(str, Enum):
    """Plan status types"""
    DRAFT = "draft"
    APPROVED = "approved"
    COMPLETED = "completed"


class PlanData(BaseModel):
    """Structured data for plan JSONB field"""
    status: PlanStatus
    markdown_content: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    id: str
    name: str
    data: PlanData  # Structured JSONB data
    version: int
    content_hash: str
    created_at: datetime
    updated_at: datetime


class PlanCreate(BaseModel):
    id: str
    name: str
    data: PlanData
    content_hash: str
    version: Optional[int] = 1


class FileError(BaseModel):
    filename: str
    error_message: str
    error_type: str


class PlanLoadResult(BaseModel):
    files: dict[str, str]
    errors: Optional[List[FileError]] = None  # (filename, error_message)
