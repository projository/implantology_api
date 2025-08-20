from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.message import Message, MessageCreate, MessageUpdate
# from pymongo import DESCENDING
import math

# Exception class for message not found
class MessageNotFound(Exception):
    pass


async def get_message(db: AsyncIOMotorDatabase, message_id: str) -> Message:
    message_data = await db.messages.find_one({"_id": ObjectId(message_id)})
    if message_data:
        message_data["_id"] = str(message_data["_id"])
        return Message(**message_data)
    raise MessageNotFound(f"Message with id {message_id} not found")


async def list_messages(
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

    # Fetch paginated messages
    messages_cursor = db.messages.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    messages = await messages_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for message in messages:
        message["_id"] = str(message["_id"])

    # Fetch total number of messages
    total = await db.messages.count_documents(query)

    return {
        "data": [Message(**message).dict() for message in messages],  # Or just return raw message dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }
# async def list_messages(
#     db: AsyncIOMotorDatabase,
#     last_created_at: Optional[str] = None,
#     per_page: int = 10
# ) -> List[Message]:
#     query = {}
#     if last_created_at:
#         try:
#             last_created_at_dt = datetime.fromisoformat(last_created_at)
#             query["created_at"] = {"$lt": last_created_at_dt}
#         except Exception:
#             raise ValueError("Invalid last_created_at format")

#     messages_cursor = (
#         db.messages
#         .find(query)
#         .sort("created_at", DESCENDING)
#         .limit(per_page)
#     )
#     messages = await messages_cursor.to_list(length=per_page)

#     for message in messages:
#         message["_id"] = str(message["_id"])

#     return [Message(**message) for message in messages]


async def create_message(db: AsyncIOMotorDatabase, message_create: MessageCreate) -> Message:
    message_data = message_create.dict()
    message_data["created_at"] = datetime.now()
    message_data["updated_at"] = datetime.now()
    result = await db.messages.insert_one(message_data)
    message_data["_id"] = str(result.inserted_id)
    return Message(**message_data)


async def update_message(db: AsyncIOMotorDatabase, message_id: str, message_update: MessageUpdate) -> Message:
    update_data = {k: v for k, v in message_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.messages.update_one({"_id": ObjectId(message_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_message(db, message_id)
    raise MessageNotFound(f"Message with id {message_id} not found")


async def delete_message(db: AsyncIOMotorDatabase, message_id: str):
    result = await db.messages.delete_one({"_id": ObjectId(message_id)})
    if result.deleted_count == 1:
        return True
    raise MessageNotFound(f"Message with id {message_id} not found")
