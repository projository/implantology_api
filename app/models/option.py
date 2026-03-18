from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from app.models.custom_types import PydanticObjectId


OptionType = Literal["start", "question", "answer", "end", "support"]


class OptionItem(BaseModel):
    label: str
    next_id: str  # frontend sends string


class Option(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: OptionType
    message: str
    options: Optional[List[OptionItem]] = []
    metadata: Optional[Dict] = {}
    created_at: datetime
    updated_at: datetime

    # 🔥 Used by frontend to trigger support flow
    is_support: Optional[bool] = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class OptionCreate(BaseModel):
    type: OptionType
    message: str
    options: Optional[List[OptionItem]] = []


class OptionUpdate(BaseModel):
    message: Optional[str] = None
    options: Optional[List[OptionItem]] = None