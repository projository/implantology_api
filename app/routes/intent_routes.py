# app/routes/intent_routes.py

from fastapi import APIRouter, HTTPException, UploadFile, status, Query, Depends, File
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.intent import (
    Intent,
    ResponseIntent,
    IntentCreate,
    IntentUpdate,
)
from app.crud.intent_crud import (
    create_intent,
    get_intent,
    get_intents,
    update_intent,
    delete_intent,
    upload_intents,
    delete_all_intents,
    IntentNotFound,
)
from app.utils.database import get_database
from app.models.pagination import PaginatedResponse


router = APIRouter()


async def get_db():
    return await get_database()


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    file_bytes = await file.read()

    result = await upload_intents(db, file_bytes)

    return {
        "message": "Upload completed",
        **result
    }


@router.delete("/clear")
async def remove_all_intents(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    deleted_count = await delete_all_intents(db)

    return {
        "message": "All intents deleted successfully",
        "deleted_count": deleted_count
    }


@router.get("", response_model=PaginatedResponse[ResponseIntent])
async def list_intents(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_intents(db, page, per_page, keyword)


@router.post("", response_model=Intent, status_code=status.HTTP_201_CREATED)
async def add_intent(
    intent_create: IntentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await create_intent(db, intent_create)


@router.get("/{intent_id}", response_model=Intent)
async def read_intent(intent_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await get_intent(db, intent_id)
    except IntentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{intent_id}", response_model=Intent)
async def modify_intent(
    intent_id: str,
    intent_update: IntentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await update_intent(db, intent_id, intent_update)
    except IntentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{intent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_intent(
    intent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_intent(db, intent_id)
    except IntentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None