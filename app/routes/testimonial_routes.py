from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.testimonial import Testimonial, TestimonialCreate, TestimonialUpdate
from app.crud.testimonial_crud import (
    get_testimonials,
    create_testimonial,
    get_testimonial,
    update_testimonial,
    delete_testimonial,
    TestimonialNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Testimonial])
async def list_testimonials(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    testimonials = await get_testimonials(db, page, per_page, keyword)
    return testimonials


@router.post("", response_model=Testimonial, status_code=status.HTTP_201_CREATED)
async def add_testimonial(
    testimonial_create: TestimonialCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    testimonial = await create_testimonial(db, testimonial_create)
    return testimonial


@router.get("/{testimonial_id}", response_model=Testimonial)
async def read_testimonial(testimonial_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        testimonial = await get_testimonial(db, testimonial_id)
        return testimonial
    except TestimonialNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{testimonial_id}", response_model=Testimonial)
async def modify_testimonial(
    testimonial_id: str,
    testimonial_update: TestimonialUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        testimonial = await update_testimonial(db, testimonial_id, testimonial_update)
        return testimonial
    except TestimonialNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_testimonial(
    testimonial_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_testimonial(db, testimonial_id)
    except TestimonialNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
