from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.category import Category
from app.models.custom_types import PydanticObjectId
from app.models.instructor import Instructor

class Data(BaseModel):
    data_type_id: str
    value: str

class Variant(BaseModel):
    title: str
    description: str
    price: int

class Course(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: str
    category_id: str
    category: Optional[Category] = None
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    location: str
    is_free: bool
    duration: Optional[str] = None
    start_at: datetime
    end_at: datetime
    title: str
    description: str
    price: int
    offer_start_at: Optional[datetime] = None
    offer_end_at: Optional[datetime] = None
    offer_price: Optional[int] = 0
    variants: List[Variant]
    instructor_ids: List[str]
    instructors: Optional[List[Instructor]] = []
    language: str
    students: Optional[int] = 0
    comments: Optional[int] = 0
    lectures: int
    quizzes: int
    assessments: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class CourseCreate(BaseModel):
    type: str
    category_id: str
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    location: str
    is_free: bool
    start_at: datetime
    end_at: datetime
    title: str
    description: str
    price: int
    offer_start_at: Optional[datetime] = None
    offer_end_at: Optional[datetime] = None
    offer_price: Optional[int] = 0
    variants: List[Variant]
    instructor_ids: List[str]
    language: str
    lectures: int
    quizzes: int
    assessments: bool


class CourseUpdate(BaseModel):
    type: Optional[str] = None
    category_id: Optional[str] = None
    image_key: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    desc: Optional[List[Data]] = None
    location: Optional[str] = None
    is_free: Optional[bool] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    offer_start_at: Optional[datetime] = None
    offer_end_at: Optional[datetime] = None
    offer_price: Optional[int] = 0
    variants: Optional[List[Variant]] = None
    instructor_ids: Optional[List[str]] = None
    language: Optional[str] = None
    lectures: Optional[int] = None
    quizzes: Optional[int] = None
    assessments: Optional[bool] = None
