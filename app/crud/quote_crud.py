from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.quote import Quote, QuoteCreate, QuoteUpdate
import math


# Exception class for quote not found
class QuoteNotFound(Exception):
    pass


async def get_quote(db: AsyncIOMotorDatabase, quote_id: str) -> Quote:
    quote_data = await db.quotes.find_one({"_id": ObjectId(quote_id)})
    if quote_data:
        quote_data["_id"] = str(quote_data["_id"])
        return Quote(**quote_data)
    raise QuoteNotFound(f"Quote with id {quote_id} not found")


async def list_quotes(
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
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in title
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated quotes
    quotes_cursor = db.quotes.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    quotes = await quotes_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for quote in quotes:
        quote["_id"] = str(quote["_id"])

    # Fetch total number of quotes
    total = await db.quotes.count_documents(query)

    return {
        "data": [Quote(**quote).dict() for quote in quotes],  # Or just return raw quote dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }

async def create_quote(db: AsyncIOMotorDatabase, quote_create: QuoteCreate) -> Quote:
    quote_data = quote_create.dict()
    quote_data["created_at"] = datetime.now()
    quote_data["updated_at"] = datetime.now()
    result = await db.quotes.insert_one(quote_data)
    quote_data["_id"] = str(result.inserted_id)
    return Quote(**quote_data)


async def update_quote(db: AsyncIOMotorDatabase, quote_id: str, quote_update: QuoteUpdate) -> Quote:
    update_data = {k: v for k, v in quote_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.quotes.update_one({"_id": ObjectId(quote_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_quote(db, quote_id)
    raise QuoteNotFound(f"Quote with id {quote_id} not found")


async def delete_quote(db: AsyncIOMotorDatabase, quote_id: str):
    result = await db.quotes.delete_one({"_id": ObjectId(quote_id)})
    if result.deleted_count == 1:
        return True
    raise QuoteNotFound(f"Quote with id {quote_id} not found")
