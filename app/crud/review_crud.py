from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.review import Review, ReviewCreate, ReviewUpdate
import math


# Exception class for review not found
class ReviewNotFound(Exception):
    pass


async def list_reviews(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Build the MongoDB query
    query = {}
    if search_key:
        query = {
            "$or": [
                {"type": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated reviews
    reviews_cursor = db.reviews.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    reviews = await reviews_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for review in reviews:
        review["_id"] = str(review["_id"])

    # Fetch total number of reviews
    total = await db.reviews.count_documents(query)

    return {
        "data": [Review(**review).dict() for review in reviews],  # Or just return raw review dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }

async def create_review(db: AsyncIOMotorDatabase, review_create: ReviewCreate) -> Review:
    review_data = review_create.dict()
    review_data["created_at"] = datetime.now()
    review_data["updated_at"] = datetime.now()
    result = await db.reviews.insert_one(review_data)
    review_data["_id"] = str(result.inserted_id)
    return Review(**review_data)


async def get_review(db: AsyncIOMotorDatabase, review_id: str) -> Review:
    review_data = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if review_data:
        review_data["_id"] = str(review_data["_id"])
        return Review(**review_data)
    raise ReviewNotFound(f"Review with id {review_id} not found")


async def update_review(db: AsyncIOMotorDatabase, review_id: str, review_update: ReviewUpdate) -> Review:
    update_data = {k: v for k, v in review_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_review(db, review_id)
    raise ReviewNotFound(f"Review with id {review_id} not found")


async def delete_review(db: AsyncIOMotorDatabase, review_id: str):
    result = await db.reviews.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 1:
        return True
    raise ReviewNotFound(f"Review with id {review_id} not found")
