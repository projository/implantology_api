from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId

class Category(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class CategoryCreate(BaseModel):
    type: str
    name: str


class CategoryUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
