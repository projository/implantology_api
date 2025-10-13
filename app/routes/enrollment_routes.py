from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate
from app.crud.enrollment_crud import (
    get_enrollments,
    create_enrollment,
    get_enrollment,
    update_enrollment,
    delete_enrollment,
    EnrollmentNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()

async def get_db():
    db = await get_database()
    return db


@router.get("", response_model=PaginatedResponse[Enrollment])
async def list_enrollments(
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enrollments = await get_enrollments(
        db, 
        str(current_user["_id"]), 
        str(current_user["role"]), 
        type, 
        page, 
        per_page, 
        keyword
    )
    return enrollments


@router.post("", response_model=Enrollment, status_code=status.HTTP_201_CREATED)
async def add_enrollment(
    enrollment_create: EnrollmentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enrollment = await create_enrollment(db, str(current_user["_id"]), enrollment_create)
    return enrollment


@router.get("/{enrollment_id}", response_model=Enrollment)
async def read_enrollment(
    enrollment_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        enrollment = await get_enrollment(db, enrollment_id)
        return enrollment
    except EnrollmentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{enrollment_id}", response_model=Enrollment)
async def modify_enrollment(
    enrollment_id: str,
    enrollment_update: EnrollmentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        enrollment = await update_enrollment(db, enrollment_id, enrollment_update)
        return enrollment
    except EnrollmentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enrollment(
    enrollment_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_enrollment(db, enrollment_id)
    except EnrollmentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
