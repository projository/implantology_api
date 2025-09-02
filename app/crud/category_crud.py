from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.category import Category, CategoryCreate, CategoryUpdate
import math

# Exception class for category not found
class CategoryNotFound(Exception):
    pass


async def get_category(db: AsyncIOMotorDatabase, category_id: str) -> Category:
    category_data = await db.categories.find_one({"_id": ObjectId(category_id)})
    if category_data:
        category_data["_id"] = str(category_data["_id"])
        return Category(**category_data)
    raise CategoryNotFound(f"Category with id {category_id} not found")


async def list_categories(
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
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated categories
    categories_cursor = db.categories.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    categories = await categories_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for category in categories:
        category["_id"] = str(category["_id"])

    # Fetch total number of categories
    total = await db.categories.count_documents(query)

    return {
        "data": [Category(**category).dict() for category in categories],  # Or just return raw category dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_category(db: AsyncIOMotorDatabase, category_create: CategoryCreate) -> Category:
    category_data = category_create.dict()
    category_data["created_at"] = datetime.now()
    category_data["updated_at"] = datetime.now()
    result = await db.categories.insert_one(category_data)
    category_data["_id"] = str(result.inserted_id)
    return Category(**category_data)


async def update_category(db: AsyncIOMotorDatabase, category_id: str, category_update: CategoryUpdate) -> Category:
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_category(db, category_id)
    raise CategoryNotFound(f"Category with id {category_id} not found")


async def delete_category(db: AsyncIOMotorDatabase, category_id: str):
    result = await db.categories.delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 1:
        return True
    raise CategoryNotFound(f"Category with id {category_id} not found")
