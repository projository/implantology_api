from fastapi import APIRouter, Depends, HTTPException, status
from app.models.constant import Constant, ConstantSet
from app.crud.constant_crud import (
    get_constant,
    set_constant,
    ConstantNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read constant
@router.get("", response_model=Constant)
async def read_constant(db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        constant = await get_constant(db)
        return constant
    except ConstantNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Write constant
@router.post("", response_model=Constant, status_code=status.HTTP_201_CREATED)
async def write_constant(
    constant_set: ConstantSet,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        constant = await set_constant(db, constant_set)
        return constant
    except ConstantNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))