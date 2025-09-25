from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime
from app.models.custom_types import PydanticObjectId
from app.models.user import User


RatingInt = Annotated[int, Field(ge=1, le=5)]

class Review(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    type: str
    type_id: str
    user: Optional[User] = None
    rating: RatingInt
    message: str
    like_id: Optional[List[str]] = []
    dislike_id: Optional[List[str]] = []
    replayer: Optional[User] = None
    replay_message: Optional[str] = None
    replay_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class ReviewCreate(BaseModel):
    type: str
    type_id: str
    rating: RatingInt
    message: str
    

class ReviewReplay(BaseModel):
    replay_message: Optional[str] = None