from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class PromptPlanStatus(str, Enum):
    """Plan status types"""
    DRAFT = "draft"
    APPROVED = "approved"
    COMPLETED = "completed"


class PromptType(str, Enum):
    """Prompt types"""
    PLAN = "plan"
    CMD = "cmd"


class CmdCategory(str, Enum):
    GO = "go"
    PYTHON = "python"
    JS = "js"
    ARCHIVE = "archive"
    TOOLS = "tools"
    MCP = "mcp"
    UNCATEGORIZED = "uncategorized"


class PromptData(BaseModel):
    """Structured data for prompt JSONB field"""
    type: PromptType
    status: PromptPlanStatus
    project: Optional[str]
    cmd_category: Optional[CmdCategory]
    content: str  # Markdown content for plans, command content for cmds
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Prompt(BaseModel):
    id: str
    name: str
    data: PromptData  # Structured JSONB data
    version: int
    content_hash: str
    created_at: datetime
    updated_at: datetime


class PromptCreate(BaseModel):
    id: str
    name: str
    data: PromptData
    content_hash: str
    version: Optional[int] = 1


class LoadError(BaseModel):
    filename: str
    error_message: str
    error_type: str


class PromptCreateResult(BaseModel):
    """Result of creating a new prompt"""
    success: bool
    prompt_id: str
    version: int
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class PromptLoadResult(BaseModel):
    """Result of loading prompts into database"""
    loaded_prompts: List[Prompt]
    errors: Optional[List[LoadError]] = None
