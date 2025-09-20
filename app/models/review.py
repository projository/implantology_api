from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal
from app.models.custom_types import PydanticObjectId


RatingFloat = Annotated[float, Field(ge=1, le=5)]

class Review(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: str
    type_id: str
    review_id: Optional[str] = None
    user_id: str
    rating: Optional[RatingFloat] = None
    message: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ReviewCreate(BaseModel):
    type: str
    type_id: str
    review_id: Optional[str] = None
    user_id: str
    rating: Optional[RatingFloat] = None
    message: str


class ReviewUpdate(BaseModel):
    type: Optional[str] = None
    type_id: Optional[str] = None
    review_id: Optional[str] = None
    user_id: Optional[str] = None
    rating: Optional[RatingFloat] = None
    message: Optional[str] = None
