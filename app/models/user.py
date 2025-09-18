from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.custom_types import PydanticObjectId


class User(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    role: str
    image_key: str
    full_name: str
    email: EmailStr
    phone_number: str
    gender: str
    age: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class UserCreate(BaseModel):
    role: str
    image_key: Optional[str]
    full_name: str
    email: EmailStr
    phone_number: str
    password: str
    gender: Optional[str]
    age: Optional[str]


class UserUpdate(BaseModel):
    role: Optional[str]
    image_key: Optional[str]
    full_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    password: Optional[str]
    gender: Optional[str]
    age: Optional[str]
