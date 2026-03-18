from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from app.models.custom_types import PydanticObjectId


OptionType = Literal["start", "question", "answer", "end", "support"]


class OptionItem(BaseModel):
    label: str
    next_id: str


class Option(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: OptionType
    message: str
    options: Optional[List[OptionItem]] = Field(default_factory=list)
    metadata: Optional[Dict] = Field(default_factory=dict)
    is_support: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class OptionCreate(BaseModel):
    type: OptionType
    message: str
    options: Optional[List[OptionItem]] = Field(default_factory=list)


class OptionUpdate(BaseModel):
    message: Optional[str] = None
    options: Optional[List[OptionItem]] = None