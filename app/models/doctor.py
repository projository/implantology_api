from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId

class Doctor(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    name: str
    sub_text: str
    description: str
    image_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class DoctorCreate(BaseModel):
    name: str
    sub_text: str
    description: str
    image_key: str


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    sub_text: Optional[str] = None
    description: Optional[str] = None
    image_key: Optional[str] = None
