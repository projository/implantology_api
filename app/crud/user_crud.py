from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.user import User, UserCreate, UserUpdate
import math

from app.utils.auth import hash_password


# Exception class for user not found
class UserNotFound(Exception):
    pass


async def get_users(
    db: AsyncIOMotorDatabase,
    role: str,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Base query → filter by role
    query: Dict[str, Any] = {"role": role}

    # Add search filter if provided
    if search_key:
        query["$or"] = [
            {"name": {"$regex": search_key, "$options": "i"}},
            {"email": {"$regex": search_key, "$options": "i"}},
            {"phone_number": {"$regex": search_key, "$options": "i"}},
        ]

    # Fetch paginated users
    users_cursor = db.users.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    users = await users_cursor.to_list(length=per_page)

    # Convert ObjectId → str
    for user in users:
        user["_id"] = str(user["_id"])

    # Count total
    total = await db.users.count_documents(query)

    return {
        "data": [User(**user).dict() for user in users],
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        },
    }


async def create_user(db: AsyncIOMotorDatabase, user_create: UserCreate) -> User | None:
    user_data = user_create.dict()
    
    user_data["password"] = hash_password(user_data["password"])
    user_data["created_at"] = datetime.now()
    user_data["updated_at"] = datetime.now()
    
    result = await db.users.insert_one(user_data)
    if not result.inserted_id:
        return None
    
    user_data["_id"] = str(result.inserted_id)
    return User(**user_data)


async def get_user(db: AsyncIOMotorDatabase, user_id: str) -> User:
    user_data = await db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        user_data["_id"] = str(user_data["_id"])
        return User(**user_data)
    raise UserNotFound(f"User with id {user_id} not found")


async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: UserUpdate) -> User:
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}

    # Only hash the password if it exists in the update data
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
    
    update_data["updated_at"] = datetime.now()
    result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_user(db, user_id)
    raise UserNotFound(f"User with id {user_id} not found")


async def delete_user(db: AsyncIOMotorDatabase, user_id: str):
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return True
    raise UserNotFound(f"User with id {user_id} not found")
