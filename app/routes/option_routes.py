from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.pagination import PaginatedResponse
from app.utils.database import get_database
from app.models.option import Option, OptionCreate, OptionUpdate
from app.crud.option_crud import (
    create_option,
    get_options,
    update_option,
    delete_option,
    start_flow,
    next_flow,
    get_option,
    OptionNotFound
)

router = APIRouter()


async def get_db():
    return await get_database()


@router.get("/start", response_model=Option)
async def start_chat(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await start_flow(db)


@router.get("/next/{next_id}", response_model=Option)
async def next_chat(next_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await next_flow(db, next_id)
    except OptionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=PaginatedResponse[Option])
async def list_options(
    type: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    options = await get_options(db, page, per_page, type)
    return options


@router.post("", response_model=Option, status_code=status.HTTP_201_CREATED)
async def create_option(option: OptionCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await create_option(db, option)


@router.get("/{option_id}", response_model=Option)
async def get_option(option_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await get_option(db, option_id)
    except OptionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{option_id}", response_model=Option)
async def update_option(option_id: str, option: OptionUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await update_option(db, option_id, option)
    except OptionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(option_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        await delete_option(db, option_id)
    except OptionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None