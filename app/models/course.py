from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Course(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class CourseCreate(BaseModel):
    name: str


class CourseUpdate(BaseModel):
    name: Optional[str] = None