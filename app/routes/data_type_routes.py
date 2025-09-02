from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.data_type import DataType, DataTypeCreate, DataTypeUpdate
from app.crud.data_type_crud import (
    get_data_type,
    list_data_types,
    create_data_type,
    update_data_type,
    delete_data_type,
    DataTypeNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read data_type by ID
@router.get("/{data_type_id}", response_model=DataType)
async def read_data_type(data_type_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        data_type = await get_data_type(db, data_type_id)
        return data_type
    except DataTypeNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all data_type
@router.get("", response_model=PaginatedResponse[DataType])
async def list_all_data_types(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    data_types = await list_data_types(db, page, per_page, keyword)
    return data_types


# Create a new data_type
@router.post("", response_model=DataType, status_code=status.HTTP_201_CREATED)
async def create_new_data_type(
    data_type_create: DataTypeCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data_type = await create_data_type(db, data_type_create)
    return data_type


# Update an existing data_type
@router.put("/{data_type_id}", response_model=DataType)
async def update_existing_data_type(
    data_type_id: str,
    data_type_update: DataTypeUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        data_type = await update_data_type(db, data_type_id, data_type_update)
        return data_type
    except DataTypeNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a data_type
@router.delete("/{data_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_data_type(
    data_type_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_data_type(db, data_type_id)
    except DataTypeNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
