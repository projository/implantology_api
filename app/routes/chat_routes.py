# app/routes/chat_routes.py

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.chat import Chat, ChatCreate
from app.crud.chat_crud import (
    create_chat,
    get_chat,
    list_chats,
    ChatNotFound,
)
from app.utils.database import get_database

router = APIRouter()


async def get_db():
    return await get_database()


@router.get("", response_model=list[Chat])
async def get_chats(
    user_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await list_chats(db, user_id)


@router.post("", response_model=Chat)
async def create_chat(
    chat_create: ChatCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await create_chat(db, chat_create)


@router.get("/{chat_id}", response_model=Chat)
async def read_chat(
    chat_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await get_chat(db, chat_id)
    except ChatNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))