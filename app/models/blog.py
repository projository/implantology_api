from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.category import Category
from app.models.custom_types import PydanticObjectId
from app.models.doctor import Doctor

class Data(BaseModel):
    data_type_id: str
    value: str


class Blog(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    category_id: str
    category: Optional[Category] = None
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    doctor_id: str
    doctor: Optional[Doctor] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class BlogCreate(BaseModel):
    category_id: str
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    doctor_id: str


class BlogUpdate(BaseModel):
    category_id: Optional[str] = None
    image_key: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    desc: Optional[List[Data]] = None
    doctor_id: Optional[str] = None