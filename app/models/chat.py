# app/models/chat.py

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.models.custom_types import PydanticObjectId


ChatStatus = Literal["open", "pending_admin", "closed", "archived"]
ChatSource = Literal["bot", "human", "hybrid"]


class Chat(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")

    user_id: str
    user_name: Optional[str] = None
    user_image_key: Optional[str] = None

    status: ChatStatus = "open"
    source: ChatSource = "bot"

    assigned_admin_id: Optional[str] = None
    escalated_at: Optional[datetime] = None

    last_message: Optional[str] = None
    last_message_at: datetime

    unread_admin_count: int = 0
    unread_user_count: int = 0

    is_bot_enabled: bool = True

    failure_count: int = 0
    current_intent_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ChatCreate(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    user_image_key: Optional[str] = None


class ChatUpdate(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    assigned_admin_id: Optional[str] = None
    is_bot_enabled: Optional[bool] = None