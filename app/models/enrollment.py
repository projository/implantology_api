from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId
from app.models.user import User
from app.models.course import Course


class Enrollment(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    user: Optional[User] = None
    course: Optional[Dict[str, Any]] = None
    payment_id: str
    order_id: str
    signature: str
    status: str
    amount: int
    currency: str
    start_at: datetime
    end_at: datetime
    stage: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class EnrollmentCreate(BaseModel):
    course_id: str
    payment_id: str
    order_id: str
    signature: str
    status: str
    amount: int
    currency: str


class EnrollmentUpdate(BaseModel):
    course_id: Optional[str] = None
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    signature: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
