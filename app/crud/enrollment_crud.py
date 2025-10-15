from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate
import math


# Exception class for enrollment not found
class EnrollmentNotFound(Exception):
    pass


async def get_enrollments(
    db: AsyncIOMotorDatabase,
    user_id: str,
    role: str,
    type: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page
    now = datetime.utcnow()

    # Base query
    query: Dict[str, Any] = {}

    # Optional text search
    if search_key:
        query["$or"] = [
            {"payment_id": {"$regex": search_key, "$options": "i"}},
            {"order_id": {"$regex": search_key, "$options": "i"}},
        ]

    if role.upper() == "CLIENT":
        # Always filter by the current user
        query["user_id"] = user_id

        if type:
            type_upper = type.upper()

            if type_upper == "COMPLETED":
                # COMPLETED = already ended
                query["end_at"] = {"$lt": now}

            elif type_upper == "ONGOING":
                # ONGOING = currently ongoing (start_at <= now <= end_at)
                query["$and"] = [
                    {"start_at": {"$lte": now}},
                    {"end_at": {"$gte": now}}
                ]

            elif type_upper == "UPCOMING":
                # UPCOMING = not yet started (start_at > now)
                query["start_at"] = {"$gt": now}

    # if role.upper() == "CLIENT":
    #     if not type:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Please provide a 'type' parameter to filter enrollments"
    #         )
    #     # Filter enrollments for the current user
    #     query["user_id"] = user_id

    #     if type.upper() == "INACTIVE":
    #         # INACTIVE = already ended
    #         query["end_at"] = {"$lt": now}

    #     elif type.upper() == "ACTIVE":
    #         # ACTIVE = ongoing (start_at <= now <= end_at) OR upcoming (start_at > now)
    #         query["$or"] = [
    #             {"$and": [{"start_at": {"$lte": now}}, {"end_at": {"$gte": now}}]},  # ongoing
    #             {"start_at": {"$gt": now}}  # upcoming
    #         ]

    # --------------------- Aggregation Pipeline ---------------------
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},

        # Convert string IDs to ObjectId for lookups
        {
            "$addFields": {
                "user_obj_id": {"$toObjectId": "$user_id"},
                "course_obj_id": {"$toObjectId": "$course_id"},
            }
        },

        # Lookup user info
        {
            "$lookup": {
                "from": "users",
                "localField": "user_obj_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},

        # Lookup course info
        {
            "$lookup": {
                "from": "courses",
                "localField": "course_obj_id",
                "foreignField": "_id",
                "as": "course",
            }
        },
        {"$unwind": {"path": "$course", "preserveNullAndEmptyArrays": True}},

        # Add stage field dynamically
        {
            "$addFields": {
                "stage": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$end_at", now]}, "then": "COMPLETED"},
                            {"case": {"$and": [{"$lte": ["$start_at", now]}, {"$gte": ["$end_at", now]}]}, "then": "ONGOING"},
                            {"case": {"$gt": ["$start_at", now]}, "then": "UPCOMING"},
                        ],
                        "default": "UNKNOWN"
                    }
                }
            }
        },

        # Final projection for clean response
        {
            "$project": {
                "_id": 1,
                "user": 1,
                "course": {
                    "$cond": [
                        {"$ifNull": ["$course._id", False]},
                        {
                            "_id": "$course._id",
                            "name": "$course.name",
                            "short_desc": "$course.short_desc",
                            "location": "$course.location",
                        },
                        None,
                    ]
                },
                "payment_id": 1,
                "order_id": 1,
                "signature": 1,
                "status": 1,
                "amount": 1,
                "currency": 1,
                "start_at": 1,
                "end_at": 1,
                "stage": 1,  # include stage
                "created_at": 1,
                "updated_at": 1,
            }
        },
    ]

    # Execute aggregation
    enrollments_cursor = db.enrollments.aggregate(pipeline)
    enrollments = await enrollments_cursor.to_list(length=per_page)

    # Convert ObjectIds → strings
    for enrollment in enrollments:
        if "_id" in enrollment:
            enrollment["_id"] = str(enrollment["_id"])
        if enrollment.get("user") and "_id" in enrollment["user"]:
            enrollment["user"]["_id"] = str(enrollment["user"]["_id"])
        if enrollment.get("course") and "_id" in enrollment["course"]:
            enrollment["course"]["_id"] = str(enrollment["course"]["_id"])

    # Pagination
    total = await db.enrollments.count_documents(query)

    return {
        "data": enrollments,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        },
    }


async def create_enrollment(
    db: AsyncIOMotorDatabase,
    user_id: str,
    enrollment_create: EnrollmentCreate,
) -> Enrollment:
    enrollment_data = enrollment_create.dict()
    
    enrollment_data["user_id"] = user_id
    enrollment_data["created_at"] = datetime.now()
    enrollment_data["updated_at"] = datetime.now()

    # Fetch course details
    course = await db.courses.find_one({"_id": ObjectId(enrollment_create.course_id)})
    if not course:
        raise ValueError("Course not found")
    
    enrollment_data["start_at"] = course["start_at"]
    enrollment_data["end_at"] = course["end_at"]

    result = await db.enrollments.insert_one(enrollment_data)
    enrollment_data["_id"] = str(result.inserted_id)

    return Enrollment(**enrollment_data)


async def get_enrollment(
    db: Any,  # AsyncIOMotorDatabase
    enrollment_id: str,
) -> Enrollment:
    pipeline = [
        {"$match": {"_id": ObjectId(enrollment_id)}},

        # Prepare object ids
        {
            "$addFields": {
                "user_obj_id": {"$toObjectId": "$user_id"},
                "course_obj_id": {"$toObjectId": "$course_id"},
            }
        },

        # Lookup user
        {
            "$lookup": {
                "from": "users",
                "localField": "user_obj_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},

        # Lookup course
        {
            "$lookup": {
                "from": "courses",
                "localField": "course_obj_id",
                "foreignField": "_id",
                "as": "course"
            }
        },
        {"$unwind": {"path": "$course", "preserveNullAndEmptyArrays": True}},

        # Final projection
        {
            "$project": {
                "_id": 1,
                "user": 1,
                "course": {
                    "$cond": [
                        {"$ifNull": ["$course._id", False]},
                        {
                            "_id": "$course._id",
                            "name": "$course.name",
                            "short_desc": "$course.short_desc",
                            "location": "$course.location",
                        },
                        None,
                    ]
                },
                "payment_id": 1,
                "order_id": 1,
                "signature": 1,
                "status": 1,
                "amount": 1,
                "currency": 1,
                "start_at": 1,
                "end_at": 1,
                "created_at": 1,
                "updated_at": 1,
            }
        }
    ]

    cursor = db.enrollments.aggregate(pipeline)
    enrollment_data = await cursor.to_list(length=1)

    if not enrollment_data: 
        raise EnrollmentNotFound(f"Enrollment with id {enrollment_id} not found")

    enrollment = enrollment_data[0]

    # Convert ObjectIds to string
    if "_id" in enrollment:
        enrollment["_id"] = str(enrollment["_id"])
    if enrollment.get("user") and "_id" in enrollment["user"]:
        enrollment["user"]["_id"] = str(enrollment["user"]["_id"])
    if enrollment.get("course") and enrollment["course"] and "_id" in enrollment["course"]:
        enrollment["course"]["_id"] = str(enrollment["course"]["_id"])

    return Enrollment(**enrollment)


async def update_enrollment(
    db: AsyncIOMotorDatabase,
    enrollment_id: str,
    enrollment_update: EnrollmentUpdate
) -> Enrollment:
    update_data = {k: v for k, v in enrollment_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()

    result = await db.enrollments.update_one(
        {"_id": ObjectId(enrollment_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise EnrollmentNotFound(f"Enrollment with id {enrollment_id} not found")

    return await get_enrollment(db, enrollment_id)


async def delete_enrollment(db: AsyncIOMotorDatabase, enrollment_id: str):
    result = await db.enrollments.delete_one({"_id": ObjectId(enrollment_id)})
    if result.deleted_count == 1:
        return True
    raise EnrollmentNotFound(f"Enrollment with id {enrollment_id} not found")
