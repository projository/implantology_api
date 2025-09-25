from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.review import Review, ReviewCreate, ReviewReplay
from app.crud.review_crud import (
    list_reviews,
    create_review,
    get_review,
    replay_review,
    react_review,
    delete_review,
    ReviewNotFound,
)
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Review])
async def list_all_reviews(
    type: str,
    type_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    reviews = await list_reviews(db, type, type_id, page, per_page)
    return reviews


@router.post("", response_model=Review, status_code=status.HTTP_201_CREATED)
async def create_new_review(
    review_create: ReviewCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = await create_review(db, str(current_user["_id"]), review_create)
    return review


@router.get("/{review_id}", response_model=Review)
async def read_review(review_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        review = await get_review(db, review_id)
        return review
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{review_id}/replay", response_model=Review)
async def replay_to_review(
    review_id: str,
    review_replay: ReviewReplay,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        review = await replay_review(db, review_id, str(current_user["_id"]), review_replay)
        return review
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{review_id}/{react_as}", response_model=Review)
async def replay_to_review(
    review_id: str,
    react_as: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await react_review(db, review_id, str(current_user["_id"]), react_as)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

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
