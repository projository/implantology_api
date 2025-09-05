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
    pipeline = [
        {"$match": {"_id": ObjectId(course_id)}},

        # Convert string IDs to ObjectId for lookups
        {"$addFields": {
            "instructor_obj_id": {"$toObjectId": "$instructor_id"},
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup instructor
        {
            "$lookup": {
                "from": "instructors",
                "localField": "instructor_obj_id",
                "foreignField": "_id",
                "as": "instructor"
            }
        },
        {"$unwind": {"path": "$instructor", "preserveNullAndEmptyArrays": True}},

        # Lookup category
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_obj_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
    ]

    cursor = db.courses.aggregate(pipeline)
    course_data = await cursor.to_list(length=1)

    if not course_data:
        raise CourseNotFound(f"Course with id {course_id} not found")

    course = course_data[0]

    # Convert ObjectIds to str
    course["_id"] = str(course["_id"])
    if "instructor" in course and course["instructor"]:
        course["instructor"]["_id"] = str(course["instructor"]["_id"])
    if "category" in course and course["category"]:
        course["category"]["_id"] = str(course["category"]["_id"])

    return Course(**course)


async def list_courses(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Build query
    query: Dict[str, Any] = {}
    if search_key:
        query = {
            "$or": [
                {"name": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Aggregation pipeline with $lookup for instructor and category
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},

        # Convert string IDs to ObjectId
        {"$addFields": {
            "instructor_obj_id": {"$toObjectId": "$instructor_id"},
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup instructor
        {
            "$lookup": {
                "from": "instructors",
                "localField": "instructor_obj_id",
                "foreignField": "_id",
                "as": "instructor"
            }
        },
        {"$unwind": {"path": "$instructor", "preserveNullAndEmptyArrays": True}},

        # Lookup category
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_obj_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
    ]

    # Run aggregation
    courses_cursor = db.courses.aggregate(pipeline)
    courses = await courses_cursor.to_list(length=per_page)

    # Convert ObjectIds to strings
    for course in courses:
        if "_id" in course:
            course["_id"] = str(course["_id"])
        if "instructor" in course and course["instructor"]:
            if "_id" in course["instructor"]:
                course["instructor"]["_id"] = str(course["instructor"]["_id"])
        if "category" in course and course["category"]:
            if "_id" in course["category"]:
                course["category"]["_id"] = str(course["category"]["_id"])

    # Count total for pagination
    total = await db.courses.count_documents(query)

    return {
        "data": [Course(**course) for course in courses],  # Validate against Course schema
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        }
    }


async def create_course(db: AsyncIOMotorDatabase, course_create: CourseCreate) -> Course:
    course_data = course_create.dict()
    course_data["created_at"] = datetime.now()
    course_data["updated_at"] = datetime.now()
    result = await db.courses.insert_one(course_data)
    course_data["_id"] = str(result.inserted_id)
    return Course(**course_data)


async def update_course(
    db: AsyncIOMotorDatabase,
    course_id: str,
    course_update: CourseUpdate
) -> Course:
    update_data = {k: v for k, v in course_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()

    result = await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise CourseNotFound(f"Course with id {course_id} not found")

    return await get_course(db, course_id)


async def delete_course(db: AsyncIOMotorDatabase, course_id: str):
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    if result.deleted_count == 1:
        return True
    raise CourseNotFound(f"Course with id {course_id} not found")
