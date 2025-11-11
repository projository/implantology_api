from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId

class FAQ(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    category_id: str
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class FAQCreate(BaseModel):
    category_id: str
    question: str
    answer: str


class FAQUpdate(BaseModel):
    category_id: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
