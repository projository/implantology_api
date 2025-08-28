from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId
from decimal import Decimal

class Data(BaseModel):
    type: str
    value: str

    # heading
    # sub_heading
    # paragraph
    # bullet
    # image
    # table


class Course(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    duration: str
    price: Decimal
    instructor: str
    language: str
    lectures: int
    quizzes: int
    assessments: int
    students: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            PydanticObjectId: str, 
            Decimal: lambda v: str(v)
        }


class CourseCreate(BaseModel):
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    duration: str
    price: Decimal
    instructor: str
    language: str
    lectures: int
    quizzes: int
    assessments: int
    students: int


class CourseUpdate(BaseModel):
    image_key: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    desc: Optional[List[Data]] = None
    duration: Optional[str] = None
    price: Optional[Decimal] = None
    instructor: Optional[str] = None
    language: Optional[str] = None
    lectures: Optional[int] = None
    quizzes: Optional[int] = None
    assessments: Optional[int] = None
    students: Optional[int] = None