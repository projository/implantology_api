from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.custom_types import PydanticObjectId

class Carousel(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    title: str
    description: str
    label: str
    link: str
    image_key: str
    order_number: int = Field(default=0)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class CarouselCreate(BaseModel):
    title: str
    description: str
    label: str
    link: str
    image_key: str
    order_number: int = Field(default=0)


class CarouselUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    link: Optional[str] = None
    image_key: Optional[str] = None
    order_number: Optional[int] = Field(default=0)