from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.faq import FAQ, FAQCreate, FAQUpdate
from app.crud.faq_crud import (
    get_faqs,
    create_faq,
    get_faq,
    update_faq,
    delete_faq,
    FAQNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[FAQ])
async def list_faqs(
    category_id: str = Query(None),   
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    faqs = await get_faqs(db, category_id, page, per_page, keyword)
    return faqs


@router.post("", response_model=FAQ, status_code=status.HTTP_201_CREATED)
async def add_faq(
    faq_create: FAQCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    faq = await create_faq(db, faq_create)
    return faq


@router.get("/{faq_id}", response_model=FAQ)
async def read_faq(faq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        faq = await get_faq(db, faq_id)
        return faq
    except FAQNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{faq_id}", response_model=FAQ)
async def modify_faq(
    faq_id: str,
    faq_update: FAQUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        faq = await update_faq(db, faq_id, faq_update)
        return faq
    except FAQNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_faq(
    faq_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_faq(db, faq_id)
    except FAQNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
