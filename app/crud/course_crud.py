from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.course import Course, CourseCreate, CourseUpdate
import math


# Exception class for course not found
class CourseNotFound(Exception):
    pass


async def get_course(db: AsyncIOMotorDatabase, course_id: str) -> Course:
    course_data = await db.courses.find_one({"_id": ObjectId(course_id)})
    if course_data:
        course_data["_id"] = str(course_data["_id"])
        return Course(**course_data)
    raise CourseNotFound(f"Course with id {course_id} not found")


async def list_courses(
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

    # Fetch paginated courses
    courses_cursor = db.courses.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    courses = await courses_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for course in courses:
        course["_id"] = str(course["_id"])

    # Fetch total number of courses
    total = await db.courses.count_documents(query)

    return {
        "data": [Course(**course).dict() for course in courses],  # Or just return raw course dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }

async def create_course(db: AsyncIOMotorDatabase, course_create: CourseCreate) -> Course:
    course_data = course_create.dict()
    course_data["created_at"] = datetime.now()
    course_data["updated_at"] = datetime.now()
    result = await db.courses.insert_one(course_data)
    course_data["_id"] = str(result.inserted_id)
    return Course(**course_data)


async def update_course(db: AsyncIOMotorDatabase, course_id: str, course_update: CourseUpdate) -> Course:
    update_data = {k: v for k, v in course_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_course(db, course_id)
    raise CourseNotFound(f"Course with id {course_id} not found")


async def delete_course(db: AsyncIOMotorDatabase, course_id: str):
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    if result.deleted_count == 1:
        return True
    raise CourseNotFound(f"Course with id {course_id} not found")
