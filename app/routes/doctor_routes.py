from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.doctor import Doctor, DoctorCreate, DoctorUpdate
from app.crud.doctor_crud import (
    get_doctors,
    create_doctor,
    get_doctor,
    update_doctor,
    delete_doctor,
    DoctorNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    

@router.get("", response_model=PaginatedResponse[Doctor])
async def list_doctors(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    doctors = await get_doctors(db, page, per_page, keyword)
    return doctors


@router.post("", response_model=Doctor, status_code=status.HTTP_201_CREATED)
async def add_doctor(
    doctor_create: DoctorCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doctor = await create_doctor(db, doctor_create)
    return doctor


@router.get("/{doctor_id}", response_model=Doctor)
async def read_doctor(doctor_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        doctor = await get_doctor(db, doctor_id)
        return doctor
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{doctor_id}", response_model=Doctor)
async def modify_doctor(
    doctor_id: str,
    doctor_update: DoctorUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        doctor = await update_doctor(db, doctor_id, doctor_update)
        return doctor
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_doctor(
    doctor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_doctor(db, doctor_id)
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
