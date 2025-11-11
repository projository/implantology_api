from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.course import Course, CourseCreate, CourseUpdate
from app.crud.course_crud import (
    get_courses,
    create_course,
    get_course,
    update_course,
    delete_course,
    CourseNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Course])
async def list_courses(
    type: str = Query(None),   
    is_free: str = Query(None),   
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    courses = await get_courses(db, type, is_free, keyword, page, per_page)
    return courses


@router.post("", response_model=Course, status_code=status.HTTP_201_CREATED)
async def add_course(
    course_create: CourseCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    course = await create_course(db, course_create)
    return course


@router.get("/{course_id}", response_model=Course)
async def read_course(course_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        course = await get_course(db, course_id)
        return course
    except CourseNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{course_id}", response_model=Course)
async def modify_course(
    course_id: str,
    course_update: CourseUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        course = await update_course(db, course_id, course_update)
        return course
    except CourseNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course(
    course_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_course(db, course_id)
    except CourseNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
