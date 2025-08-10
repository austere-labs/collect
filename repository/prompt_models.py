from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from config import Config


class PromptPlanStatus(str, Enum):
    """Plan status types"""

    DRAFT = "draft"
    APPROVED = "approved"
    COMPLETED = "completed"


class PromptType(str, Enum):
    """Prompt types"""

    PLAN = "plan"
    CMD = "cmd"


def create_cmd_category_enum():
    """Create CmdCategory enum dynamically from config"""
    try:
        config = Config()
        subdirs = config.command_subdirs
    except Exception:
        # Fallback to default subdirs if config fails
        subdirs = ["archive", "go", "js", "mcp", "python", "tools"]

    # Build enum members dictionary
    members = {}
    for subdir in subdirs:
        members[subdir.upper()] = subdir

    # Always include UNCATEGORIZED as fallback
    members["UNCATEGORIZED"] = "uncategorized"

    # Create enum using the functional API with type=str for JSON serialization
    return Enum("CmdCategory", members, type=str)


# Create the enum instance
CmdCategory = create_cmd_category_enum()


class Project(BaseModel):
    id: str
    github_url: str
    description: str


class PromptData(BaseModel):
    """Structured data for prompt JSONB field"""

    type: PromptType
    status: PromptPlanStatus
    project: Optional[str]
    cmd_category: Optional[CmdCategory]
    content: str  # This is the prompt content, in markdown
    description: Optional[str] = None
    # using 'claude' or 'gemini' here to specify the dir it will write to
    # .claude/commands and .gemini/commands respectively
    tags: List[str] = Field(default_factory=list)


class Prompt(BaseModel):
    id: str
    name: str
    project_id: Optional[str]
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


class PromptDeleteResult(BaseModel):
    success: bool
    prompt_id: str
    deleted: bool
    rows_affected: int
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class PromptFlattenResult(BaseModel):
    """Result of flattening a prompt to disk"""

    success: bool
    prompt_id: str
    prompt_name: str
    file_path: str
    cmd_category: str
    error_message: Optional[str] = None
    error_type: Optional[str] = None
