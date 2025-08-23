from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Testimonial(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    message: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class TestimonialCreate(BaseModel):
    message: str
    name: str


class TestimonialUpdate(BaseModel):
    message: Optional[str] = None
    name: Optional[str] = None