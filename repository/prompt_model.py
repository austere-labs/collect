from datetime import datetime
from typing import Dict, Optional
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
