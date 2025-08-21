from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.doctor import Doctor, DoctorCreate, DoctorUpdate
from app.crud.doctor_crud import (
    get_doctor,
    list_doctors,
    create_doctor,
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
    
# Read doctor by ID
@router.get("/{doctor_id}", response_model=Doctor)
async def read_doctor(doctor_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        doctor = await get_doctor(db, doctor_id)
        return doctor
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all doctor
@router.get("", response_model=PaginatedResponse[Doctor])
async def list_all_doctors(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    doctors = await list_doctors(db, page, per_page, keyword)
    return doctors


# Create a new doctor
@router.post("", response_model=Doctor, status_code=status.HTTP_201_CREATED)
async def create_new_doctor(
    doctor_create: DoctorCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doctor = await create_doctor(db, doctor_create)
    return doctor


# Update an existing doctor
@router.put("/{doctor_id}", response_model=Doctor)
async def update_existing_doctor(
    doctor_id: str,
    doctor_update: DoctorUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        doctor = await update_doctor(db, doctor_id, doctor_update)
        return doctor
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a doctor
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_doctor(
    doctor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_doctor(db, doctor_id)
    except DoctorNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
