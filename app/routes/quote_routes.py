from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.quote import Quote, QuoteCreate, QuoteUpdate
from app.crud.quote_crud import (
    get_quote,
    list_quotes,
    create_quote,
    update_quote,
    delete_quote,
    QuoteNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read quote by ID
@router.get("/{quote_id}", response_model=Quote)
async def read_quote(quote_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        quote = await get_quote(db, quote_id)
        return quote
    except QuoteNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all quote
@router.get("", response_model=PaginatedResponse[Quote])
async def list_all_quotes(
    keyword: str = Query(None),   
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    quotes = await list_quotes(db, page, per_page, keyword)
    return quotes


# Create a new quote
@router.post("", response_model=Quote, status_code=status.HTTP_201_CREATED)
async def create_new_quote(
    quote_create: QuoteCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    quote = await create_quote(db, quote_create)
    return quote


# Update an existing quote
@router.put("/{quote_id}", response_model=Quote)
async def update_existing_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        quote = await update_quote(db, quote_id, quote_update)
        return quote
    except QuoteNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a quote
@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_quote(
    quote_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_quote(db, quote_id)
    except QuoteNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
