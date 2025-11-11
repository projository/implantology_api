from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.gallery import Gallery, GalleryCreate
from app.crud.gallery_crud import (
    get_galleries,
    create_gallery,
    delete_gallery,
    GalleryNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Gallery])
async def list_galleries(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    is_patient: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    galleries = await get_galleries(db, page, per_page, keyword, is_patient)
    return galleries


@router.post("", response_model=List[Gallery], status_code=status.HTTP_201_CREATED)
async def add_gallery(
    gallery_create: GalleryCreate,
    is_patient: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    gallery = await create_gallery(db, gallery_create, is_patient)
    return gallery


@router.delete("/{gallery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_gallery(
    gallery_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_gallery(db, gallery_id)
    except GalleryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
