from typing import Dict, Any, List, Optional
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.gallery import Gallery, GalleryCreate
import math

# Exception class for gallery not found
class GalleryNotFound(Exception):
    pass


async def get_galleries(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None,
    is_patient: Optional[bool] = False,
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Base query
    query: Dict[str, Any] = {}

    # Add search filter
    if search_key:
        query["$or"] = [
            {"image_key": {"$regex": search_key, "$options": "i"}},
            # Add more searchable fields if needed
        ]

    # Add patient/main filter
    query["type"] = "patient" if is_patient else "main"

    # Fetch paginated galleries
    galleries_cursor = (
        db.galleries.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(per_page)
    )
    galleries = await galleries_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for gallery in galleries:
        gallery["_id"] = str(gallery["_id"])

    # Count total
    total = await db.galleries.count_documents(query)

    return {
        "data": [Gallery(**gallery).dict() for gallery in galleries],  # Or just galleries if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        },
    }


async def create_gallery(
    db: AsyncIOMotorDatabase,
    gallery_create: GalleryCreate,
    is_patient: Optional[bool] = False,
) -> List[Gallery]:
    galleries = []

    # 1. Get all image_keys from request
    image_keys = gallery_create.image_keys

    # 2. Find existing keys in DB
    existing_docs = await db.galleries.find(
        {
            "image_key": {"$in": image_keys},
            "type": "patient" if is_patient else "main"
        },
        {"image_key": 1, "_id": 0}
    ).to_list(None)
    existing_keys = {doc["image_key"] for doc in existing_docs}

    # 3. Filter only new image_keys
    unique_keys = [key for key in image_keys if key not in existing_keys]

    if not unique_keys:
        return []  # nothing new to insert

    # 4. Build new gallery docs
    now = datetime.now()
    gallery_docs = [
        {
            "image_key": key,
            "type": "patient" if is_patient else "main",
            "created_at": now,
            "updated_at": now,
        }
        for key in unique_keys
    ]

    # 5. Insert new docs
    result = await db.galleries.insert_many(gallery_docs)

    # 6. Attach inserted IDs
    for key, _id in zip(unique_keys, result.inserted_ids):
        gallery_docs[unique_keys.index(key)]["_id"] = str(_id)
        galleries.append(Gallery(**gallery_docs[unique_keys.index(key)]))

    return galleries


async def delete_gallery(db: AsyncIOMotorDatabase, gallery_id: str):
    result = await db.galleries.delete_one({"_id": ObjectId(gallery_id)})
    if result.deleted_count == 1:
        return True
    raise GalleryNotFound(f"Gallery with id {gallery_id} not found")
