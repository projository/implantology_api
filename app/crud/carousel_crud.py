from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.carousel import Carousel, CarouselCreate, CarouselUpdate
import math

# Exception class for carousel not found
class CarouselNotFound(Exception):
    pass


async def get_carousels(
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
                {"title": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated carousels
    carousels_cursor = db.carousels.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    carousels = await carousels_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for carousel in carousels:
        carousel["_id"] = str(carousel["_id"])

    # Fetch total number of carousels
    total = await db.carousels.count_documents(query)

    return {
        "data": [Carousel(**carousel).dict() for carousel in carousels],  # Or just return raw carousel dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }
# async def get_carousels(
#     db: AsyncIOMotorDatabase,
#     page: int = 1,
#     per_page: int = 10,
#     search_key: Optional[str] = None
# ) -> Dict[str, Any]:
#     skip = (page - 1) * per_page

#     # Build the MongoDB query
#     query = {}
#     if search_key:
#         query = {
#             "$or": [
#                 {"title": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
#                 # Add more fields here if needed, e.g.:
#                 # {"description": {"$regex": search_key, "$options": "i"}}
#             ]
#         }

#     # Fetch filtered and paginated carousels
#     carousels_cursor = db.carousels.find(query).sort("created_at", -1).skip(skip).limit(per_page)
#     carousels = await carousels_cursor.to_list(length=per_page)

#     # Convert ObjectId to str
#     for carousel in carousels:
#         carousel["_id"] = str(carousel["_id"])

#     # Total matching documents
#     total = await db.carousels.count_documents(query)

#     return {
#         "data": [Carousel(**carousel).dict() for carousel in carousels],
#         "pagination": {
#             "current_page": page,
#             "per_page": per_page,
#             "total": total,
#             "last_page": math.ceil(total / per_page) if per_page else 0
#         }
#     }


async def create_carousel(db: AsyncIOMotorDatabase, carousel_create: CarouselCreate) -> Carousel:
    carousel_data = carousel_create.dict()
    carousel_data["created_at"] = datetime.now()
    carousel_data["updated_at"] = datetime.now()
    result = await db.carousels.insert_one(carousel_data)
    carousel_data["_id"] = str(result.inserted_id)
    return Carousel(**carousel_data)


async def get_carousel(db: AsyncIOMotorDatabase, carousel_id: str) -> Carousel:
    carousel_data = await db.carousels.find_one({"_id": ObjectId(carousel_id)})
    if carousel_data:
        carousel_data["_id"] = str(carousel_data["_id"])
        return Carousel(**carousel_data)
    raise CarouselNotFound(f"Carousel with id {carousel_id} not found")


async def update_carousel(db: AsyncIOMotorDatabase, carousel_id: str, carousel_update: CarouselUpdate) -> Carousel:
    update_data = {k: v for k, v in carousel_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.carousels.update_one({"_id": ObjectId(carousel_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_carousel(db, carousel_id)
    raise CarouselNotFound(f"Carousel with id {carousel_id} not found")


async def delete_carousel(db: AsyncIOMotorDatabase, carousel_id: str):
    result = await db.carousels.delete_one({"_id": ObjectId(carousel_id)})
    if result.deleted_count == 1:
        return True
    raise CarouselNotFound(f"Carousel with id {carousel_id} not found")
