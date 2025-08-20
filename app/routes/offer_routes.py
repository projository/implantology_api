from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.offer import Offer, OfferCreate, OfferUpdate
from app.crud.offer_crud import (
    get_offer,
    list_offers,
    create_offer,
    update_offer,
    delete_offer,
    OfferNotFound,
)
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.pagination import PaginatedResponse

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db
    
# Read offer by ID
@router.get("/{offer_id}", response_model=Offer)
async def read_offer(offer_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        offer = await get_offer(db, offer_id)
        return offer
    except OfferNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# List all offer
@router.get("", response_model=PaginatedResponse[Offer])
async def list_all_offers(   
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    offers = await list_offers(db, page, per_page, keyword)
    return offers


# Create a new offer
@router.post("", response_model=Offer, status_code=status.HTTP_201_CREATED)
async def create_new_offer(
    offer_create: OfferCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    offer = await create_offer(db, offer_create)
    return offer


# Update an existing offer
@router.put("/{offer_id}", response_model=Offer)
async def update_existing_offer(
    offer_id: str,
    offer_update: OfferUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        offer = await update_offer(db, offer_id, offer_update)
        return offer
    except OfferNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete a offer
@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_offer(
    offer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        await delete_offer(db, offer_id)
    except OfferNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
