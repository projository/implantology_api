from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.blog import Blog, BlogCreate, BlogUpdate
from app.crud.blog_crud import (
    get_blog,
    list_blogs,
    create_blog,
    update_blog,
    delete_blog,
    BlogNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read blog by ID
@router.get("/{blog_id}", response_model=Blog)
async def read_blog(blog_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        blog = await get_blog(db, blog_id)
        return blog
    except BlogNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all blog
@router.get("", response_model=PaginatedResponse[Blog])
async def list_all_blogs(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    blogs = await list_blogs(db, page, per_page, keyword)
    return blogs


# Create a new blog
@router.post("", response_model=Blog, status_code=status.HTTP_201_CREATED)
async def create_new_blog(
    blog_create: BlogCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    blog = await create_blog(db, blog_create)
    return blog


# Update an existing blog
@router.put("/{blog_id}", response_model=Blog)
async def update_existing_blog(
    blog_id: str,
    blog_update: BlogUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        blog = await update_blog(db, blog_id, blog_update)
        return blog
    except BlogNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a blog
@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_blog(
    blog_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_blog(db, blog_id)
    except BlogNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
