from datetime import date
from typing import List, Optional
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class PromptModel(BaseModel):
    id: Optional[int] = None
    prompt_uuid: str
    version: int
    content: str
    metadata: Dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


class PromptCreateModel(BaseModel):
    name: str
    content: str
    metadata: Optional[Dict] = Field(default_factory=dict)


class PromptResponseModel(BaseModel):
    id: int
    prompt_uuid: str
    version: int
    content: str
    metadata: Dict
    created_at: datetime
    updated_at: datetime
    is_active: bool


class FileError(BaseModel):
    filename: str
    error_message: str
    error_type: str


class LoadResult(BaseModel):
    files: Dict[str, str]
    errors: Optional[List[FileError]] = None  # (filename, error_message)


class PromptFrontmatter(BaseModel):
    """Pydantic model for prompt frontmatter metadata"""

    title: str = Field(..., description="The title of the prompt")
    tags: List[str] = Field(default_factory=list,
                            description="List of tags for categorization")
    version: float = Field(..., description="Version number of the prompt")
    author: str = Field(..., description="Author of the prompt")
    created: date = Field(...,
                          description="Creation date in YYYY-MM-DD format")
    description: str = Field(...,
                             description="Brief description of the prompt's purpose")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "My Prompt",
                "tags": ["ai", "automation", "coding"],
                "version": 1.0,
                "author": "John Doe",
                "created": "2024-01-15",
                "description": "A prompt for code generation"
            }
        }
