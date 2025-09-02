from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.instructor import Instructor, InstructorCreate, InstructorUpdate
from app.crud.instructor_crud import (
    get_instructor,
    list_instructors,
    create_instructor,
    update_instructor,
    delete_instructor,
    InstructorNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read instructor by ID
@router.get("/{instructor_id}", response_model=Instructor)
async def read_instructor(instructor_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        instructor = await get_instructor(db, instructor_id)
        return instructor
    except InstructorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all instructor
@router.get("", response_model=PaginatedResponse[Instructor])
async def list_all_instructors(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    instructors = await list_instructors(db, page, per_page, keyword)
    return instructors


# Create a new instructor
@router.post("", response_model=Instructor, status_code=status.HTTP_201_CREATED)
async def create_new_instructor(
    instructor_create: InstructorCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    instructor = await create_instructor(db, instructor_create)
    return instructor


# Update an existing instructor
@router.put("/{instructor_id}", response_model=Instructor)
async def update_existing_instructor(
    instructor_id: str,
    instructor_update: InstructorUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        instructor = await update_instructor(db, instructor_id, instructor_update)
        return instructor
    except InstructorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a instructor
@router.delete("/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_instructor(
    instructor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_instructor(db, instructor_id)
    except InstructorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
