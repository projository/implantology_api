from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.data_type import DataType, DataTypeCreate, DataTypeUpdate
import math


# Exception class for data_type not found
class DataTypeNotFound(Exception):
    pass


async def get_data_types(
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

    # Fetch paginated data_types
    data_types_cursor = db.data_types.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    data_types = await data_types_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for data_type in data_types:
        data_type["_id"] = str(data_type["_id"])

    # Fetch total number of data_types
    total = await db.data_types.count_documents(query)

    return {
        "data": [DataType(**data_type).dict() for data_type in data_types],  # Or just return raw data_type dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_data_type(db: AsyncIOMotorDatabase, data_type_create: DataTypeCreate) -> DataType:
    data_type_data = data_type_create.dict()
    data_type_data["created_at"] = datetime.now()
    data_type_data["updated_at"] = datetime.now()
    result = await db.data_types.insert_one(data_type_data)
    data_type_data["_id"] = str(result.inserted_id)
    return DataType(**data_type_data)


async def get_data_type(db: AsyncIOMotorDatabase, data_type_id: str) -> DataType:
    data_type_data = await db.data_types.find_one({"_id": ObjectId(data_type_id)})
    if data_type_data:
        data_type_data["_id"] = str(data_type_data["_id"])
        return DataType(**data_type_data)
    raise DataTypeNotFound(f"DataType with id {data_type_id} not found")


async def update_data_type(db: AsyncIOMotorDatabase, data_type_id: str, data_type_update: DataTypeUpdate) -> DataType:
    update_data = {k: v for k, v in data_type_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.data_types.update_one({"_id": ObjectId(data_type_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_data_type(db, data_type_id)
    raise DataTypeNotFound(f"DataType with id {data_type_id} not found")


async def delete_data_type(db: AsyncIOMotorDatabase, data_type_id: str):
    result = await db.data_types.delete_one({"_id": ObjectId(data_type_id)})
    if result.deleted_count == 1:
        return True
    raise DataTypeNotFound(f"DataType with id {data_type_id} not found")
