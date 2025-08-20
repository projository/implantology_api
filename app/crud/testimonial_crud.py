from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.testimonial import Testimonial, TestimonialCreate, TestimonialUpdate
import math


# Exception class for testimonial not found
class TestimonialNotFound(Exception):
    pass


async def get_testimonial(db: AsyncIOMotorDatabase, testimonial_id: str) -> Testimonial:
    testimonial_data = await db.testimonials.find_one({"_id": ObjectId(testimonial_id)})
    if testimonial_data:
        testimonial_data["_id"] = str(testimonial_data["_id"])
        return Testimonial(**testimonial_data)
    raise TestimonialNotFound(f"Testimonial with id {testimonial_id} not found")


async def list_testimonials(
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
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated testimonials
    testimonials_cursor = db.testimonials.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    testimonials = await testimonials_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for testimonial in testimonials:
        testimonial["_id"] = str(testimonial["_id"])

    # Fetch total number of testimonials
    total = await db.testimonials.count_documents(query)

    return {
        "data": [Testimonial(**testimonial).dict() for testimonial in testimonials],  # Or just return raw testimonial dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }

async def create_testimonial(db: AsyncIOMotorDatabase, testimonial_create: TestimonialCreate) -> Testimonial:
    testimonial_data = testimonial_create.dict()
    testimonial_data["created_at"] = datetime.now()
    testimonial_data["updated_at"] = datetime.now()
    result = await db.testimonials.insert_one(testimonial_data)
    testimonial_data["_id"] = str(result.inserted_id)
    return Testimonial(**testimonial_data)


async def update_testimonial(db: AsyncIOMotorDatabase, testimonial_id: str, testimonial_update: TestimonialUpdate) -> Testimonial:
    update_data = {k: v for k, v in testimonial_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.testimonials.update_one({"_id": ObjectId(testimonial_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_testimonial(db, testimonial_id)
    raise TestimonialNotFound(f"Testimonial with id {testimonial_id} not found")


async def delete_testimonial(db: AsyncIOMotorDatabase, testimonial_id: str):
    result = await db.testimonials.delete_one({"_id": ObjectId(testimonial_id)})
    if result.deleted_count == 1:
        return True
    raise TestimonialNotFound(f"Testimonial with id {testimonial_id} not found")
