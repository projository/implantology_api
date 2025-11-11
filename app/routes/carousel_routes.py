from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.carousel import Carousel, CarouselCreate, CarouselUpdate
from app.crud.carousel_crud import (
    get_carousels,
    create_carousel,
    get_carousel,
    update_carousel,
    delete_carousel,
    CarouselNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Carousel])
async def list_carousels(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    carousels = await get_carousels(db, page, per_page, keyword)
    return carousels


@router.post("", response_model=Carousel, status_code=status.HTTP_201_CREATED)
async def add_carousel(
    carousel_create: CarouselCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    carousel = await create_carousel(db, carousel_create)
    return carousel


@router.get("/{carousel_id}", response_model=Carousel)
async def read_carousel(carousel_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        carousel = await get_carousel(db, carousel_id)
        return carousel
    except CarouselNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{carousel_id}", response_model=Carousel)
async def modify_carousel(
    carousel_id: str,
    carousel_update: CarouselUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        carousel = await update_carousel(db, carousel_id, carousel_update)
        return carousel
    except CarouselNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{carousel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_carousel(
    carousel_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_carousel(db, carousel_id)
    except CarouselNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
