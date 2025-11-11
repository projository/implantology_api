from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.pagination import PaginatedResponse
from app.models.message import Message, MessageCreate, MessageUpdate
from app.crud.message_crud import (
    get_messages,
    create_message,
    get_message,
    update_message,
    delete_message,
    MessageNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Message])
async def list_messages(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    messages = await get_messages(db, page, per_page, keyword)
    return messages
# async def list_messages(
#     last_created_at: Optional[str] = Query(None),
#     per_page: int = Query(10, ge=1, le=100),
#     db: AsyncIOMotorDatabase = Depends(get_db)
# ):
#     messages = await get_messages(db, last_created_at, per_page)
#     return messages


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
async def add_message(
    message_create: MessageCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    message = await create_message(db, message_create)
    return message


@router.get("/{message_id}", response_model=Message)
async def read_message(message_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        message = await get_message(db, message_id)
        return message
    except MessageNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{message_id}", response_model=Message)
async def modify_message(
    message_id: str,
    message_update: MessageUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        message = await update_message(db, message_id, message_update)
        return message
    except MessageNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_message(
    message_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_message(db, message_id)
    except MessageNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
