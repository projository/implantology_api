from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.crud.category_crud import (
    get_category,
    list_categories,
    create_category,
    update_category,
    delete_category,
    CategoryNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read category by ID
@router.get("/{category_id}", response_model=Category)
async def read_category(category_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        category = await get_category(db, category_id)
        return category
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all category
@router.get("", response_model=PaginatedResponse[Category])
async def list_all_categories(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    categories = await list_categories(db, page, per_page, keyword)
    return categories


# Create a new category
@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    category_create: CategoryCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    category = await create_category(db, category_create)
    return category


# Update an existing category
@router.put("/{category_id}", response_model=Category)
async def update_existing_category(
    category_id: str,
    category_update: CategoryUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        category = await update_category(db, category_id, category_update)
        return category
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a category
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_category(
    category_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_category(db, category_id)
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
