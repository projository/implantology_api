from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Constant(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    name: Optional[str] = None
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}

    
class ConstantSet(BaseModel):
    name: Optional[str] = None
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None