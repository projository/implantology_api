# app/models/intent.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Intent(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    intent: str
    requests: List[str] = Field(default_factory=list)
    responses: List[str] = Field(default_factory=list)

    # 🔥 NEW: One embedding per request
    request_embeddings: List[List[float]] = Field(default_factory=list)

    priority: int = 0
    is_active: bool = True
    is_fallback: bool = False

    match_count: int = 0
    last_matched: Optional[datetime] = None

    positive_feedback: int = 0
    negative_feedback: int = 0

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ResponseIntent(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    intent: str
    requests: List[str] = Field(default_factory=list)
    responses: List[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class IntentCreate(BaseModel):
    intent: str
    requests: List[str] = Field(default_factory=list)
    responses: List[str] = Field(default_factory=list)
    priority: int = 0
    is_active: bool = True


class IntentUpdate(BaseModel):
    intent: Optional[str] = None
    requests: Optional[List[str]] = None
    responses: Optional[List[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None