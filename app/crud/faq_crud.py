from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.faq import FAQ, FAQCreate, FAQUpdate
import math

# Exception class for faq not found
class FAQNotFound(Exception):
    pass


async def get_faqs(
    db: AsyncIOMotorDatabase,
    category_id: str,
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
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    if category_id:
        query["category_id"] = category_id

    # Fetch paginated faqs
    faqs_cursor = db.faqs.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    faqs = await faqs_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for faq in faqs:
        faq["_id"] = str(faq["_id"])

    # Fetch total number of faqs
    total = await db.faqs.count_documents(query)

    return {
        "data": [FAQ(**faq).dict() for faq in faqs],  # Or just return raw faq dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_faq(db: AsyncIOMotorDatabase, faq_create: FAQCreate) -> FAQ:
    faq_data = faq_create.dict()
    faq_data["created_at"] = datetime.now()
    faq_data["updated_at"] = datetime.now()
    result = await db.faqs.insert_one(faq_data)
    faq_data["_id"] = str(result.inserted_id)
    return FAQ(**faq_data)


async def get_faq(db: AsyncIOMotorDatabase, faq_id: str) -> FAQ:
    faq_data = await db.faqs.find_one({"_id": ObjectId(faq_id)})
    if faq_data:
        faq_data["_id"] = str(faq_data["_id"])
        return FAQ(**faq_data)
    raise FAQNotFound(f"FAQ with id {faq_id} not found")


async def update_faq(db: AsyncIOMotorDatabase, faq_id: str, faq_update: FAQUpdate) -> FAQ:
    update_data = {k: v for k, v in faq_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.faqs.update_one({"_id": ObjectId(faq_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_faq(db, faq_id)
    raise FAQNotFound(f"FAQ with id {faq_id} not found")


async def delete_faq(db: AsyncIOMotorDatabase, faq_id: str):
    result = await db.faqs.delete_one({"_id": ObjectId(faq_id)})
    if result.deleted_count == 1:
        return True
    raise FAQNotFound(f"FAQ with id {faq_id} not found")
