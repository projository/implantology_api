# app/models/intent.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Keyword(BaseModel):
    word: str
    weight: int = 1


class Intent(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    intent: str
    examples: List[str] = Field(default_factory=list)
    keywords: List[Keyword] = Field(default_factory=list)
    responses: List[str] = Field(default_factory=list)

    priority: int = 0
    is_active: bool = True
    is_fallback: bool = False

    match_count: int = 0
    last_matched: Optional[datetime] = None

    positive_feedback: int = 0
    negative_feedback: int = 0

    user_weights: Dict[str, float] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class IntentCreate(BaseModel):
    intent: str
    examples: List[str] = []
    keywords: List[Keyword] = []
    responses: List[str] = []
    priority: int = 0
    is_active: bool = True
    is_fallback: bool = False


class IntentUpdate(BaseModel):
    intent: Optional[str] = None
    examples: Optional[List[str]] = None
    keywords: Optional[List[Keyword]] = None
    responses: Optional[List[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    is_fallback: Optional[bool] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    fallback: bool


# ───────────── Session Model (Included Here As Requested) ─────────────

class Session(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    session_id: str
    last_intent: Optional[str] = None
    last_message: Optional[str] = None
    context: Dict = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}