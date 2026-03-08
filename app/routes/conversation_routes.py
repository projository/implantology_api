# app/routes/conversation_routes.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.crud.intent_crud import generate_reply
from app.models.conversation import ResponseConversation, ConversationCreate, ConversationUpdate
from app.crud.conversation_crud import create_conversation, list_conversations, save_conversation
from app.crud.chat_crud import create_chat, get_chat
from app.models.chat import ChatCreate
from app.utils.database import get_database

router = APIRouter()


async def get_db():
    return await get_database()


@router.post("/send")
async def send_message(
    conversation_data: ConversationCreate,
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):

    # 1️⃣ Create chat if needed
    chat_id = conversation_data.chat_id

    user = await db.users.find_one({"_id": ObjectId(user_id)})

    name = user.get("first_name") if user else None
    image_key = user.get("image_key") if user else None

    if not chat_id:
        chat = await create_chat(db, ChatCreate(user_id=user_id,user_name=name,user_image_key=image_key))
        chat_id = str(chat.id)

    chat = await get_chat(db, chat_id)

    # 2️⃣ Save user conversation
    user_msg = await save_conversation(
        db=db,
        chat_id=chat_id,
        sender_type="user",
        content=conversation_data.message,
        sender_id=user_id,
    )

    # 3️⃣ If bot disabled → escalate directly
    if not chat.is_bot_enabled:
        await db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "status": "pending_admin",
                    "source": "human",
                    "escalated_at": datetime.utcnow()
                }
            }
        )

        return {
            "chat_id": chat_id,
            "status": "pending_admin",
            "message": "Your message has been sent to support."
        }

    # 4️⃣ Generate intelligent reply
    reply_data = await generate_reply(
        db,
        conversation_data.message,
        chat_id
    )

    decision = reply_data["decision"]

    # if decision in ["bot", "clarification"]:

    #     bot_msg = await save_conversation(
    #         db=db,
    #         chat_id=chat_id,
    #         sender_type="bot",
    #         content=reply_data["message"],
    #         intent_id=reply_data["intent_id"],
    #         confidence_score=reply_data["confidence"],
    #     )

    #     return {
    #         "chat_id": chat_id,
    #         "status": decision,
    #         "confidence": reply_data["confidence"],
    #         "bot_message": bot_msg,
    #     }
    
    # Bot confident reply → save conversation
    if decision == "bot":

        bot_msg = await save_conversation(
            db=db,
            chat_id=chat_id,
            sender_type="bot",
            content=reply_data["message"],
            intent_id=reply_data["intent_id"],
            confidence_score=reply_data["confidence"],
        )

        return {
            "chat_id": chat_id,
            "status": "bot",
            "confidence": reply_data["confidence"],
            "bot_message": bot_msg,
        }


    # Clarification → DO NOT SAVE
    if decision == "clarification":

        return {
            "chat_id": chat_id,
            "status": "clarification",
            "confidence": reply_data["confidence"],
            "message": reply_data["message"]
        }

    # Escalate
    await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"status": "pending_admin"}}
    )

    return {
        "chat_id": chat_id,
        "status": "pending_admin",
        "confidence": reply_data["confidence"],
        "message": reply_data["message"]
    }


@router.post("/reply")
async def replay_conversation(
    conversation_data: ConversationUpdate,
    admin_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    chat = await get_chat(db, conversation_data.chat_id)

    if chat.status not in ["pending_admin", "open"]:
        raise HTTPException(status_code=400, detail="Chat not active")

    admin_msg = await save_conversation(
        db=db,
        chat_id=conversation_data.chat_id,
        sender_type="admin",
        content=conversation_data.message,
        sender_id=admin_id,
    )

    await db.chats.update_one(
        {"_id": ObjectId(conversation_data.chat_id)},
        {
            "$set": {
                "status": "open",
                "source": "human",
                "assigned_admin_id": admin_id,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {
        "status": "admin_replied",
        "admin_message": admin_msg,
    }


@router.get("/{chat_id}", response_model=list[ResponseConversation])
async def get_conversations(
    chat_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await list_conversations(db, chat_id)