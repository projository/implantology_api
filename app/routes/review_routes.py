from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.review import Review, ReviewCreate, ReviewUpdate
from app.crud.review_crud import (
    get_review,
    list_reviews,
    create_review,
    update_review,
    delete_review,
    ReviewNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read review by ID
@router.get("/{review_id}", response_model=Review)
async def read_review(review_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        review = await get_review(db, review_id)
        return review
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all review
@router.get("", response_model=PaginatedResponse[Review])
async def list_all_reviews(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    reviews = await list_reviews(db, page, per_page, keyword)
    return reviews


# Create a new review
@router.post("", response_model=Review, status_code=status.HTTP_201_CREATED)
async def create_new_review(
    review_create: ReviewCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    review = await create_review(db, review_create)
    return review


# Update an existing review
@router.put("/{review_id}", response_model=Review)
async def update_existing_review(
    review_id: str,
    review_update: ReviewUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        review = await update_review(db, review_id, review_update)
        return review
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a review
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_review(
    review_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_review(db, review_id)
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
