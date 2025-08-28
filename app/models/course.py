from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId

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
    price: str
    instructor: str
    instructor_image_key: str
    language: str
    lectures: int
    quizzes: int
    assessments: bool
    students: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class CourseCreate(BaseModel):
    image_key: str
    name: str
    short_desc: str
    desc: List[Data]
    duration: str
    price: str
    instructor: str
    instructor_image_key: str
    language: str
    lectures: int
    quizzes: int
    assessments: bool
    students: int


class CourseUpdate(BaseModel):
    image_key: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    desc: Optional[List[Data]] = None
    duration: Optional[str] = None
    price: Optional[str] = None
    instructor: Optional[str] = None
    instructor_image_key: Optional[str] = None
    language: Optional[str] = None
    lectures: Optional[int] = None
    quizzes: Optional[int] = None
    assessments: Optional[bool] = None
    students: Optional[int] = None