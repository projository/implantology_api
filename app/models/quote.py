from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId


class Quote(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    name: str
    email: str
    phone_number: str
    company_name: Optional[str] = None
    event_type: str
    num_of_guests: str
    event_date: str
    event_time: str
    event_location: str
    latitude: str
    longitude: str
    dietary_type: str
    budget_range: str
    service_type: Optional[str] = None
    message: Optional[str] = None
    known_from: Optional[str] = None
    terms_and_conditions: bool
    privacy_policy: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class QuoteCreate(BaseModel):
    name: str
    email: str
    phone_number: str
    company_name: Optional[str] = None
    event_type: str
    num_of_guests: str
    event_date: str
    event_time: str
    event_location: str
    latitude: str
    longitude: str
    dietary_type: str
    budget_range: str
    service_type: Optional[str] = None
    message: Optional[str] = None
    known_from: Optional[str] = None
    terms_and_conditions: bool
    privacy_policy: bool


class QuoteUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    company_name: Optional[str] = None
    event_type: Optional[str] = None
    num_of_guests: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    event_location: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    dietary_type: Optional[str] = None
    budget_range: Optional[str] = None
    service_type: Optional[str] = None
    message: Optional[str] = None
    known_from: Optional[str] = None
    terms_and_conditions: Optional[bool] = None
    privacy_policy: Optional[bool] = None