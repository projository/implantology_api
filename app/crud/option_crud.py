import math
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId

from app.models.option import Option, OptionCreate, OptionUpdate


class OptionNotFound(Exception):
    pass


def serialize(option: dict) -> dict:
    option["_id"] = str(option["_id"])

    if "options" in option and option["options"]:
        for opt in option["options"]:
            if isinstance(opt.get("next_id"), ObjectId):
                opt["next_id"] = str(opt["next_id"])

    option["is_support"] = option.get("type") == "support"

    return option


async def start_flow(db: AsyncIOMotorDatabase) -> Option:
    option = await db.options.find_one({"type": "start"})

    if not option:
        raise OptionNotFound("Start option not found")

    return Option(**serialize(option))


async def next_flow(db: AsyncIOMotorDatabase, next_id: str) -> Option:
    return await get_option(db, next_id)


async def create_option(db: AsyncIOMotorDatabase, option: OptionCreate) -> Option:
    data = option.dict()

    if data.get("options"):
        for opt in data["options"]:
            opt["next_id"] = ObjectId(opt["next_id"])

    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()

    result = await db.options.insert_one(data)
    data["_id"] = result.inserted_id

    return Option(**serialize(data))


async def get_options(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    type: Optional[str] = None
) -> Dict[str, Any]:

    skip = (page - 1) * per_page

    query = {}
    if type:
        query = {"type": type}

    options_cursor = (
        db.options.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(per_page)
    )

    options = await options_cursor.to_list(length=per_page)

    total = await db.options.count_documents(query)

    return {
        "data": [Option(**serialize(option)).dict() for option in options],
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def get_option(db: AsyncIOMotorDatabase, option_id: str) -> Option:
    option = await db.options.find_one({"_id": ObjectId(option_id)})

    if not option:
        raise OptionNotFound(f"Option '{option_id}' not found")

    return Option(**serialize(option))


async def update_option(
    db: AsyncIOMotorDatabase,
    option_id: str,
    option_update: OptionUpdate
) -> Option:

    update_data = {k: v for k, v in option_update.dict().items() if v is not None}

    if update_data.get("options"):
        for opt in update_data["options"]:
            opt["next_id"] = ObjectId(opt["next_id"])

    update_data["updated_at"] = datetime.now()

    result = await db.options.update_one(
        {"_id": ObjectId(option_id)},
        {"$set": update_data}
    )

    if result.modified_count == 1:
        return await get_option(db, option_id)

    raise OptionNotFound(f"Option '{option_id}' not found")


async def delete_option(db: AsyncIOMotorDatabase, option_id: str):
    result = await db.options.delete_one({"_id": ObjectId(option_id)})

    if result.deleted_count == 1:
        return True

    raise OptionNotFound(f"Option '{option_id}' not found")