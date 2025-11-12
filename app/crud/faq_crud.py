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
    category_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Base query
    query: Dict[str, Any] = {}

    # Add search key
    if search_key:
        query["$or"] = [
            {"question": {"$regex": search_key, "$options": "i"}},
            {"answer": {"$regex": search_key, "$options": "i"}},
        ]

    # Add category filter
    if category_id:
        query["category_id"] = category_id

    # Aggregation pipeline
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},

        # Convert category_id to ObjectId
        {"$addFields": {
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup category
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_obj_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
    ]

    # Run aggregation
    faqs_cursor = db.faqs.aggregate(pipeline)
    faqs = await faqs_cursor.to_list(length=per_page)

    # Convert ObjectIds to strings
    for faq in faqs:
        if "_id" in faq:
            faq["_id"] = str(faq["_id"])
        if "category" in faq and faq["category"]:
            if "_id" in faq["category"]:
                faq["category"]["_id"] = str(faq["category"]["_id"])

    # Total count for pagination
    total = await db.faqs.count_documents(query)

    return {
        "data": [FAQ(**faq) for faq in faqs],
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        },
    }


async def create_faq(db: AsyncIOMotorDatabase, faq_create: FAQCreate) -> FAQ:
    faq_data = faq_create.dict()
    faq_data["created_at"] = datetime.now()
    faq_data["updated_at"] = datetime.now()
    result = await db.faqs.insert_one(faq_data)
    faq_data["_id"] = str(result.inserted_id)
    return FAQ(**faq_data)


async def get_faq(db: AsyncIOMotorDatabase, faq_id: str) -> FAQ:
    pipeline = [
        {"$match": {"_id": ObjectId(faq_id)}},

        # Convert string IDs to ObjectId for lookup
        {"$addFields": {
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup category
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_obj_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
    ]

    # Run aggregation
    cursor = db.faqs.aggregate(pipeline)
    faq_data = await cursor.to_list(length=1)

    if not faq_data:
        raise FAQNotFound(f"FAQ with id {faq_id} not found")

    faq = faq_data[0]

    # Convert ObjectIds to strings
    if "_id" in faq:
        faq["_id"] = str(faq["_id"])
    if "category" in faq and faq["category"]:
        if "_id" in faq["category"]:
            faq["category"]["_id"] = str(faq["category"]["_id"])

    return FAQ(**faq)


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
