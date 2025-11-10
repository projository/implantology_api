from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.custom_types import PydanticObjectId


class User(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    role: str
    image_key: Optional[str] = None
    first_name: str
    last_name: str
    city: str
    email: EmailStr
    phone_number: str
    gender: Optional[str] = None
    age: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class UserCreate(BaseModel):
    role: str
    image_key: Optional[str] = None
    first_name: str
    last_name: str
    city: str
    email: EmailStr
    phone_number: str
    password: str
    gender: Optional[str] = None
    age: Optional[str] = None


class UserUpdate(BaseModel):
    role: str
    image_key: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
