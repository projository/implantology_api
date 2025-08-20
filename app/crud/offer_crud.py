from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.offer import Offer, OfferCreate, OfferUpdate
import math


# Exception class for offer not found
class OfferNotFound(Exception):
    pass


async def get_offer(db: AsyncIOMotorDatabase, offer_id: str) -> Offer:
    offer_data = await db.offers.find_one({"_id": ObjectId(offer_id)})
    if offer_data:
        offer_data["_id"] = str(offer_data["_id"])
        return Offer(**offer_data)
    raise OfferNotFound(f"Offer with id {offer_id} not found")


async def list_offers(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Build the MongoDB query
    query = {}
    if search_key:
        query = {
            "$or": [
                {"text": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated offers
    offers_cursor = db.offers.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    offers = await offers_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for offer in offers:
        offer["_id"] = str(offer["_id"])

    # Fetch total number of offers
    total = await db.offers.count_documents(query)

    return {
        "data": [Offer(**offer).dict() for offer in offers],  # Or just return raw offer dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_offer(db: AsyncIOMotorDatabase, offer_create: OfferCreate) -> Offer:
    offer_data = offer_create.dict()
    offer_data["created_at"] = datetime.now()
    offer_data["updated_at"] = datetime.now()
    result = await db.offers.insert_one(offer_data)
    offer_data["_id"] = str(result.inserted_id)
    return Offer(**offer_data)


async def update_offer(db: AsyncIOMotorDatabase, offer_id: str, offer_update: OfferUpdate) -> Offer:
    update_data = {k: v for k, v in offer_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.offers.update_one({"_id": ObjectId(offer_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_offer(db, offer_id)
    raise OfferNotFound(f"Offer with id {offer_id} not found")


async def delete_offer(db: AsyncIOMotorDatabase, offer_id: str):
    result = await db.offers.delete_one({"_id": ObjectId(offer_id)})
    if result.deleted_count == 1:
        return True
    raise OfferNotFound(f"Offer with id {offer_id} not found")
