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


class LoadError(BaseModel):
    filename: str
    error_message: str
    error_type: str


class PlanCreateResult(BaseModel):
    """Result of creating a new plan"""
    success: bool
    plan_id: str
    version: int
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class PlanLoadResult(BaseModel):
    """Result of loading plans into database"""
    loaded_count: int
    skipped_count: int
    error_count: int
    loaded_plans: List[str] = Field(default_factory=list)  # List of plan IDs
    # List of plan IDs that already exist
    skipped_plans: List[str] = Field(default_factory=list)
    errors: Optional[List[LoadError]] = None
