from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.course import Course, CourseCreate, CourseUpdate
import math


# Exception class for course not found
class CourseNotFound(Exception):
    pass


async def get_courses(
    db: AsyncIOMotorDatabase,
    type: Optional[str] = None,
    is_free: Optional[bool] = None,
    search_key: Optional[str] = None,
    page: int = 1,
    per_page: int = 10
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

    if type:
        query["type"] = type

    if isinstance(is_free, str):
        is_free = is_free.lower() == "true"

    if is_free is not None:
        query["is_free"] = is_free

    # Aggregation pipeline with lookups
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},

        # Convert string instructor_ids/category_id to ObjectIds
        {"$addFields": {
            "instructor_obj_ids": {
                "$map": {
                    "input": "$instructor_ids",
                    "as": "id",
                    "in": {"$toObjectId": "$$id"}
                }
            },
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup instructors
        {
            "$lookup": {
                "from": "instructors",
                "localField": "instructor_obj_ids",
                "foreignField": "_id",
                "as": "instructors"
            }
        },

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

        # Lookup enrollments (students)
        {
            "$lookup": {
                "from": "enrollments",
                "let": {"courseId": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$course_id", "$$courseId"]}}},
                    {"$count": "count"}
                ],
                "as": "students"
            }
        },

        # Lookup reviews (comments)
        {
            "$lookup": {
                "from": "reviews",
                "let": {"courseId": {"$toString": "$_id"}},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$type", "COURSE"]},
                                    {"$eq": ["$type_id", "$$courseId"]}
                                ]
                            }
                        }
                    },
                    {"$count": "count"}
                ],
                "as": "comments"
            }
        },

        # Flatten counts (convert arrays to int values)
        {
            "$addFields": {
                "students": {
                    "$ifNull": [{"$arrayElemAt": ["$students.count", 0]}, 0]
                },
                "comments": {
                    "$ifNull": [{"$arrayElemAt": ["$comments.count", 0]}, 0]
                }
            }
        },
    ]

    # Run aggregation
    courses_cursor = db.courses.aggregate(pipeline)
    courses = await courses_cursor.to_list(length=per_page)

    # Convert ObjectIds to strings for frontend
    for course in courses:
        if "_id" in course:
            course["_id"] = str(course["_id"])
        if "instructors" in course and isinstance(course["instructors"], list):
            for inst in course["instructors"]:
                if "_id" in inst:
                    inst["_id"] = str(inst["_id"])
        if "category" in course and course["category"]:
            if "_id" in course["category"]:
                course["category"]["_id"] = str(course["category"]["_id"])

    # Count total courses for pagination
    total = await db.courses.count_documents(query)

    return {
        "data": [Course(**course) for course in courses],
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        }
    }


async def create_course(db: AsyncIOMotorDatabase, course_create: CourseCreate) -> Course:
    course_data = course_create.dict()

    # Calculate duration (in days or hours, as you prefer)
    start = course_create.start_at
    end = course_create.end_at

    start = course_create.start_at
    end = course_create.end_at

    if start and end:
        total_days = (end.date() - start.date()).days + 1

        # Convert to months and days
        months = total_days // 30
        days = total_days % 30

        # Build human-readable string
        if months == 0:
            duration_str = f"{days} days"
        elif days == 0:
            duration_str = f"{months} month{'s' if months > 1 else ''}"
        else:
            duration_str = f"{months} month{'s' if months > 1 else ''} {days} days"

        course_data["duration"] = duration_str
    else:
        course_data["duration"] = None
    
    course_data["created_at"] = datetime.now()
    course_data["updated_at"] = datetime.now()

    result = await db.courses.insert_one(course_data)
    course_data["_id"] = str(result.inserted_id)
    
    return Course(**course_data)


async def get_course(db: AsyncIOMotorDatabase, course_id: str) -> Course:
    pipeline = [
        {"$match": {"_id": ObjectId(course_id)}},

        # Convert string IDs to ObjectIds for lookups
        {"$addFields": {
            "instructor_obj_ids": {
                "$map": {
                    "input": "$instructor_ids",
                    "as": "id",
                    "in": {"$toObjectId": "$$id"}
                }
            },
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup multiple instructors
        {
            "$lookup": {
                "from": "instructors",
                "localField": "instructor_obj_ids",
                "foreignField": "_id",
                "as": "instructors"
            }
        },

        # Lookup single category
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_obj_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},

        # Lookup enrollments (students)
        {
            "$lookup": {
                "from": "enrollments",
                "let": {"courseId": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$course_id", "$$courseId"]}}},
                    {"$count": "count"}
                ],
                "as": "students"
            }
        },

        # Lookup reviews (comments)
        {
            "$lookup": {
                "from": "reviews",
                "let": {"courseId": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": [{"$toLower": "$type"}, "course"]},
                                    {
                                        "$or": [
                                            {"$eq": ["$type_id", "$$courseId"]},
                                            {"$eq": ["$type_id", {"$toString": "$$courseId"}]}
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    {"$count": "count"}
                ],
                "as": "comments"
            }
        },

        # Flatten counts
        {
            "$addFields": {
                "students": {
                    "$ifNull": [{"$arrayElemAt": ["$students.count", 0]}, 0]
                },
                "comments": {
                    "$ifNull": [{"$arrayElemAt": ["$comments.count", 0]}, 0]
                }
            }
        }
    ]

    cursor = db.courses.aggregate(pipeline)
    course_data = await cursor.to_list(length=1)

    if not course_data:
        raise CourseNotFound(f"Course with id {course_id} not found")

    course = course_data[0]

    # Convert ObjectIds to str for response
    course["_id"] = str(course["_id"])

    if "instructors" in course and isinstance(course["instructors"], list):
        for inst in course["instructors"]:
            if "_id" in inst:
                inst["_id"] = str(inst["_id"])

    if "category" in course and course["category"]:
        if "_id" in course["category"]:
            course["category"]["_id"] = str(course["category"]["_id"])

    return Course(**course)


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
