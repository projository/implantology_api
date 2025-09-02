from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.gallery import Gallery, GalleryCreate
import math

# Exception class for gallery not found
class GalleryNotFound(Exception):
    pass


async def list_galleries(
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
                {"image_key": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated galleries
    galleries_cursor = db.galleries.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    galleries = await galleries_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for gallery in galleries:
        gallery["_id"] = str(gallery["_id"])

    # Fetch total number of galleries
    total = await db.galleries.count_documents(query)

    return {
        "data": [Gallery(**gallery).dict() for gallery in galleries],  # Or just return raw gallery dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_gallery(db: AsyncIOMotorDatabase, gallery_create: GalleryCreate) -> List[Gallery]:
    galleries = []

    # 1. Get all image_keys from request
    image_keys = gallery_create.image_keys

    # 2. Find existing keys in DB
    existing_docs = await db.galleries.find(
        {"image_key": {"$in": image_keys}},
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
