# app/crud/conversation_crud.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.models.conversation import Conversation, ResponseConversation
from app.services.engine_service import generate_embedding


async def create_conversation(
    db: AsyncIOMotorDatabase,
    chat_id: str,
    sender_type: str,
    content: str,
    sender_id: Optional[str] = None,
    intent_id: Optional[str] = None,
    confidence_score: Optional[float] = None,
    is_fallback: bool = False,
) -> Conversation:

    now = datetime.utcnow()

    embedding = generate_embedding(content)

    data = {
        "chat_id": ObjectId(chat_id),
        "sender_type": sender_type,
        "sender_id": sender_id,
        "content": content,
        "embedding": embedding,
        "intent_id": intent_id,
        "confidence_score": confidence_score,
        "is_fallback": is_fallback,
        "created_at": now,
    }

    result = await db.conversations.insert_one(data)

    await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$set": {"last_message_at": now},
            "$inc": {
                "unread_admin_count": 1 if sender_type == "user" else 0,
                "unread_user_count": 1 if sender_type == "admin" else 0,
            },
        },
    )

    data["_id"] = str(result.inserted_id)
    data["chat_id"] = str(data["chat_id"])

    return Conversation(**data)


# async def list_conversations(
#     db: AsyncIOMotorDatabase,
#     chat_id: str,
# ):

#     cursor = db.conversations.find(
#         {"chat_id": ObjectId(chat_id)}
#     ).sort("created_at", 1)

#     items = await cursor.to_list(length=1000)

#     for m in items:
#         m["_id"] = str(m["_id"])
#         m["chat_id"] = str(m["chat_id"])

#     return [Conversation(**m) for m in items]
from bson import ObjectId

async def list_conversations(db: AsyncIOMotorDatabase, chat_id: str):

    pipeline = [
        {
            "$match": {
                "chat_id": ObjectId(chat_id)
            }
        },

        # convert sender_id string → ObjectId
        {
            "$addFields": {
                "sender_object_id": { "$toObjectId": "$sender_id" }
            }
        },

        {
            "$lookup": {
                "from": "users",
                "localField": "sender_object_id",
                "foreignField": "_id",
                "as": "sender"
            }
        },

        {
            "$unwind": {
                "path": "$sender",
                "preserveNullAndEmptyArrays": True
            }
        },

        # build sender_name
        {
            "$addFields": {
                "sender_name": {
                    "$concat": [
                        { "$ifNull": ["$sender.first_name", ""] },
                        " ",
                        { "$ifNull": ["$sender.last_name", ""] }
                    ]
                }
            }
        },

        {
            "$sort": {"created_at": 1}
        }
    ]

    cursor = db.conversations.aggregate(pipeline)
    items = await cursor.to_list(length=1000)

    for m in items:
        m["_id"] = str(m["_id"])
        m["chat_id"] = str(m["chat_id"])

    return [ResponseConversation(**m) for m in items]


async def save_conversation(
    db: AsyncIOMotorDatabase,
    chat_id: str,
    sender_type: str,
    content: str,
    sender_id: Optional[str] = None,
    intent_id: Optional[str] = None,
    confidence_score: Optional[float] = None,
    is_fallback: bool = False,
) -> Conversation:

    now = datetime.utcnow()

    embedding = generate_embedding(content)

    data = {
        "chat_id": ObjectId(chat_id),
        "sender_type": sender_type,
        "sender_id": sender_id,
        "content": content,
        "embedding": embedding,
        "intent_id": intent_id,
        "confidence_score": confidence_score,
        "is_fallback": is_fallback,
        "created_at": now,
    }

    result = await db.conversations.insert_one(data)

    # Update chat metadata
    update_data = {
        "last_message": content,
        "last_message_at": now,
        "updated_at": now,
    }

    if sender_type == "user":
        update_data["unread_admin_count"] = 1
    elif sender_type == "admin":
        update_data["unread_user_count"] = 1

    await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": update_data},
    )

    data["_id"] = str(result.inserted_id)
    data["chat_id"] = str(data["chat_id"])

    return Conversation(**data)