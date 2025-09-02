from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from app.models.custom_types import PydanticObjectId

class Gallery(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    image_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class GalleryCreate(BaseModel):
    image_keys: List[str]