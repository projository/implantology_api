# app/crud/chat_crud.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional, List

from app.models.chat import Chat, ChatCreate, ChatUpdate


class ChatNotFound(Exception):
    pass


async def create_chat(
    db: AsyncIOMotorDatabase,
    chat_create: ChatCreate,
) -> Chat:

    now = datetime.utcnow()

    data = {
        "user_id": chat_create.user_id,
        "status": "open",
        "source": "bot",
        "last_message_at": now,
        "unread_admin_count": 0,
        "unread_user_count": 0,
        "is_bot_enabled": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.chats.insert_one(data)
    data["_id"] = str(result.inserted_id)

    return Chat(**data)


async def get_chat(
    db: AsyncIOMotorDatabase,
    chat_id: str,
) -> Chat:

    chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise ChatNotFound("Chat not found")

    chat["_id"] = str(chat["_id"])
    return Chat(**chat)


async def update_chat(
    db: AsyncIOMotorDatabase,
    chat_id: str,
    chat_update: ChatUpdate,
) -> Chat:

    update_data = {k: v for k, v in chat_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    result = await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": update_data},
    )

    if result.matched_count != 1:
        raise ChatNotFound("Chat not found")

    return await get_chat(db, chat_id)


async def list_chats(
    db: AsyncIOMotorDatabase,
    user_id: Optional[str] = None,
) -> List[Chat]:

    # Build filter dynamically
    query = {}

    if user_id:
        query["user_id"] = user_id  # Convert to ObjectId if required

    cursor = (
        db.chats
        .find(query)
        .sort("updated_at", -1)
    )

    chats = await cursor.to_list(length=100)

    for c in chats:
        c["_id"] = str(c["_id"])

    return [Chat(**c) for c in chats]