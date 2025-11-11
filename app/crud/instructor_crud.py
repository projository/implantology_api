from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.instructor import Instructor, InstructorCreate, InstructorUpdate
import math

# Exception class for instructor not found
class InstructorNotFound(Exception):
    pass


async def get_instructors(
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
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated instructors
    instructors_cursor = db.instructors.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    instructors = await instructors_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for instructor in instructors:
        instructor["_id"] = str(instructor["_id"])

    # Fetch total number of instructors
    total = await db.instructors.count_documents(query)

    return {
        "data": [Instructor(**instructor).dict() for instructor in instructors],  # Or just return raw instructor dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


async def create_instructor(db: AsyncIOMotorDatabase, instructor_create: InstructorCreate) -> Instructor:
    instructor_data = instructor_create.dict()
    instructor_data["created_at"] = datetime.now()
    instructor_data["updated_at"] = datetime.now()
    result = await db.instructors.insert_one(instructor_data)
    instructor_data["_id"] = str(result.inserted_id)
    return Instructor(**instructor_data)


async def get_instructor(db: AsyncIOMotorDatabase, instructor_id: str) -> Instructor:
    instructor_data = await db.instructors.find_one({"_id": ObjectId(instructor_id)})
    if instructor_data:
        instructor_data["_id"] = str(instructor_data["_id"])
        return Instructor(**instructor_data)
    raise InstructorNotFound(f"Instructor with id {instructor_id} not found")


async def update_instructor(db: AsyncIOMotorDatabase, instructor_id: str, instructor_update: InstructorUpdate) -> Instructor:
    update_data = {k: v for k, v in instructor_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.instructors.update_one({"_id": ObjectId(instructor_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_instructor(db, instructor_id)
    raise InstructorNotFound(f"Instructor with id {instructor_id} not found")


async def delete_instructor(db: AsyncIOMotorDatabase, instructor_id: str):
    result = await db.instructors.delete_one({"_id": ObjectId(instructor_id)})
    if result.deleted_count == 1:
        return True
    raise InstructorNotFound(f"Instructor with id {instructor_id} not found")
