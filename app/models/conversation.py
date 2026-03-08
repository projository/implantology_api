# app/models/conversation.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal
from datetime import datetime
from app.models.custom_types import PydanticObjectId


SenderType = Literal["user", "bot", "admin", "system"]
MessageType = Literal["text", "image", "file", "system"]


class Conversation(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    chat_id: PydanticObjectId

    sender_type: SenderType
    sender_id: Optional[str] = None

    message_type: MessageType = "text"
    content: str

    embedding: Optional[list[float]] = None

    intent_id: Optional[str] = None
    confidence_score: Optional[float] = None
    is_fallback: bool = False

    metadata: Optional[Dict] = None

    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ResponseConversation(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    chat_id: PydanticObjectId

    sender_type: SenderType
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_image_key: Optional[str] = None

    message_type: MessageType = "text"
    content: str

    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ConversationCreate(BaseModel):
    message: str
    chat_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    message: str
    chat_id: Optional[str] = None