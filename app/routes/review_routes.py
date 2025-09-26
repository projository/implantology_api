from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.security import OAuth2PasswordBearer
from app.models.review import Review, ReviewCreate, ReviewReplay
from app.crud.review_crud import (
    get_reviews,
    get_summary,
    create_review,
    get_review,
    replay_review,
    react_review,
    delete_review,
    ReviewNotFound,
)
from app.models.user import User
from app.utils.auth import admin_required, get_current_user
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

async def get_db():
    db = await get_database()
    return db
    

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def conditional_admin_required(
    request: Request,
    type_id: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if type_id is None:
        # Only enforce admin if type_id is missing
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        # Extract token using OAuth2PasswordBearer
        token = await oauth2_scheme(request)
        user = await get_current_user(token=token, db=db)

        if user["role"] != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return user

    # type_id is present → public access
    return None


@router.get("", response_model=PaginatedResponse[Review])
async def list_reviews(
    type: str,
    type_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: Optional[User] = Depends(conditional_admin_required)
):
    reviews = await get_reviews(db, type, type_id, page, per_page)
    return reviews


@router.get("/summary", response_model=dict)
async def retrive_summary(
    type: str,
    type_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        response = await get_summary(db, type, type_id)
        return response
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=Review, status_code=status.HTTP_201_CREATED)
async def add_review(
    review_create: ReviewCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = await create_review(db, str(current_user["_id"]), review_create)
    return review


@router.get("/{review_id}", response_model=Review)
async def read_review(
    review_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
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
    admin: User = Depends(admin_required)
):
    try:
        review = await replay_review(db, review_id, str(admin["_id"]), review_replay)
        return review
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{review_id}/{react_as}", response_model=Review)
async def react_to_review(
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
async def remove_review(
    review_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: User = Depends(get_current_user)
):
    try:
        await delete_review(db, review_id)
    except ReviewNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
