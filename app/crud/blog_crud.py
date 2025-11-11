from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.blog import Blog, BlogCreate, BlogUpdate
import math


# Exception class for blog not found
class BlogNotFound(Exception):
    pass


async def get_blogs(
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

    # Aggregation pipeline with $lookup for doctor and category
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},

        # Convert string IDs to ObjectId
        {"$addFields": {
            "doctor_obj_id": {"$toObjectId": "$doctor_id"},
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup doctor
        {
            "$lookup": {
                "from": "doctors",
                "localField": "doctor_obj_id",
                "foreignField": "_id",
                "as": "doctor"
            }
        },
        {"$unwind": {"path": "$doctor", "preserveNullAndEmptyArrays": True}},

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
    blogs_cursor = db.blogs.aggregate(pipeline)
    blogs = await blogs_cursor.to_list(length=per_page)

    # Convert ObjectIds to strings
    for blog in blogs:
        if "_id" in blog:
            blog["_id"] = str(blog["_id"])
        if "doctor" in blog and blog["doctor"]:
            if "_id" in blog["doctor"]:
                blog["doctor"]["_id"] = str(blog["doctor"]["_id"])
        if "category" in blog and blog["category"]:
            if "_id" in blog["category"]:
                blog["category"]["_id"] = str(blog["category"]["_id"])

    # Count total for pagination
    total = await db.blogs.count_documents(query)

    return {
        "data": [Blog(**blog) for blog in blogs],  # Validate against Blog schema
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        }
    }


async def create_blog(db: AsyncIOMotorDatabase, blog_create: BlogCreate) -> Blog:
    blog_data = blog_create.dict()
    blog_data["created_at"] = datetime.now()
    blog_data["updated_at"] = datetime.now()
    result = await db.blogs.insert_one(blog_data)
    blog_data["_id"] = str(result.inserted_id)
    return Blog(**blog_data)


async def get_blog(db: AsyncIOMotorDatabase, blog_id: str) -> Blog:
    pipeline = [
        {"$match": {"_id": ObjectId(blog_id)}},

        # Convert string IDs to ObjectId for lookups
        {"$addFields": {
            "doctor_obj_id": {"$toObjectId": "$doctor_id"},
            "category_obj_id": {"$toObjectId": "$category_id"}
        }},

        # Lookup doctor
        {
            "$lookup": {
                "from": "doctors",
                "localField": "doctor_obj_id",
                "foreignField": "_id",
                "as": "doctor"
            }
        },
        {"$unwind": {"path": "$doctor", "preserveNullAndEmptyArrays": True}},

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

    cursor = db.blogs.aggregate(pipeline)
    blog_data = await cursor.to_list(length=1)

    if not blog_data:
        raise BlogNotFound(f"Blog with id {blog_id} not found")

    blog = blog_data[0]

    # Convert ObjectIds to str
    blog["_id"] = str(blog["_id"])
    if "doctor" in blog and blog["doctor"]:
        blog["doctor"]["_id"] = str(blog["doctor"]["_id"])
    if "category" in blog and blog["category"]:
        blog["category"]["_id"] = str(blog["category"]["_id"])

    return Blog(**blog)


async def update_blog(
    db: AsyncIOMotorDatabase,
    blog_id: str,
    blog_update: BlogUpdate
) -> Blog:
    update_data = {k: v for k, v in blog_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()

    result = await db.blogs.update_one(
        {"_id": ObjectId(blog_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise BlogNotFound(f"Blog with id {blog_id} not found")

    return await get_blog(db, blog_id)


async def delete_blog(db: AsyncIOMotorDatabase, blog_id: str):
    result = await db.blogs.delete_one({"_id": ObjectId(blog_id)})
    if result.deleted_count == 1:
        return True
    raise BlogNotFound(f"Blog with id {blog_id} not found")
