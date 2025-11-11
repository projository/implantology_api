import math
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.review import Review, ReviewCreate, ReviewReplay
from app.models.user import User


# Exception class for review not found
class ReviewNotFound(Exception):
    pass


async def get_reviews(
    db: AsyncIOMotorDatabase,
    type: str,
    type_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    query: Dict[str, Any] = {"type": type}
    if type_id:
        query["type_id"] = type_id

    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},
        {
            "$addFields": {
                "user_obj_id": {"$toObjectId": "$user_id"},
                "replayer_obj_id": {
                    "$cond": {
                        "if": {"$ifNull": ["$replayer_id", False]},
                        "then": {"$toObjectId": "$replayer_id"},
                        "else": None
                    }
                },
                "type_obj_id": {"$toObjectId": "$type_id"}
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
        # Lookup replayer
        {
            "$lookup": {
                "from": "users",
                "localField": "replayer_obj_id",
                "foreignField": "_id",
                "as": "replayer"
            }
        },
        {"$unwind": {"path": "$replayer", "preserveNullAndEmptyArrays": True}},
        # Lookup course
        {
            "$lookup": {
                "from": "courses",
                "localField": "type_obj_id",
                "foreignField": "_id",
                "as": "course"
            }
        },
        {"$unwind": {"path": "$course", "preserveNullAndEmptyArrays": True}},
        # Lookup blog
        {
            "$lookup": {
                "from": "blogs",
                "localField": "type_obj_id",
                "foreignField": "_id",
                "as": "blog"
            }
        },
        {"$unwind": {"path": "$blog", "preserveNullAndEmptyArrays": True}},
        # Project final response
        {
            "$project": {
                "_id": 1,
                "type": 1,
                "type_id": 1,
                "user": 1,
                "replayer": 1,
                "rating": 1,
                "message": 1,
                "like_id": 1,
                "dislike_id": 1,
                "replay_message": 1,
                "replay_at": 1,
                "created_at": 1,
                "updated_at": 1,
                "course": {
                    "$cond": [
                        {"$eq": ["$type", "COURSE"]},
                        {
                            "_id": "$course._id",
                            "name": "$course.name",
                            "short_desc": "$course.short_desc",
                        },
                        None,
                    ]
                },
                "blog": {
                    "$cond": [
                        {"$eq": ["$type", "BLOG"]},
                        {
                            "_id": "$blog._id",
                            "name": "$blog.name",
                            "short_desc": "$blog.short_desc",
                        },
                        None,
                    ]
                },
            }
        }
    ]

    reviews_cursor = db.reviews.aggregate(pipeline)
    reviews = await reviews_cursor.to_list(length=per_page)

    # Convert ObjectIds to string
    for review in reviews:
        if "_id" in review:
            review["_id"] = str(review["_id"])
        if review.get("user") and "_id" in review["user"]:
            review["user"]["_id"] = str(review["user"]["_id"])
        if review.get("replayer") and "_id" in review["replayer"]:
            review["replayer"]["_id"] = str(review["replayer"]["_id"])
        if review.get("course") and "_id" in review["course"]:
            review["course"]["_id"] = str(review["course"]["_id"])
        if review.get("blog") and "_id" in review["blog"]:
            review["blog"]["_id"] = str(review["blog"]["_id"])

    total = await db.reviews.count_documents(query)

    return {
        "data": reviews,  # already shaped
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0,
        },
    }


async def create_review(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    review_create: ReviewCreate,
) -> Review:
    review_data = review_create.dict()
    review_data["user_id"] = user_id
    review_data["created_at"] = datetime.now()
    review_data["updated_at"] = datetime.now()

    # Step 1: check if review already exists for (user_id, type, type_id)
    existing = await db.reviews.find_one({
        "user_id": user_id,
        "type": review_create.type,
        "type_id": review_create.type_id,
    })

    if existing:
        # Step 2: delete the old review
        await db.reviews.delete_one({"_id": existing["_id"]})

    # Step 3: insert new review
    result = await db.reviews.insert_one(review_data)
    review_data["_id"] = str(result.inserted_id)

    # Step 4: fetch user info and embed in response
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        review_data["user"] = User(**user_doc).dict()
    else:
        review_data["user"] = None

    # Step 5: fetch course/blog info based on type
    if review_create.type == "COURSE":
        course_doc = await db.courses.find_one({"_id": ObjectId(review_create.type_id)})
        if course_doc:
            review_data["course"] = {
                "_id": str(course_doc["_id"]),
                "name": course_doc.get("name"),
                "short_desc": course_doc.get("short_desc"),
            }
        else:
            review_data["course"] = None
        review_data["blog"] = None

    elif review_create.type == "BLOG":
        blog_doc = await db.blogs.find_one({"_id": ObjectId(review_create.type_id)})
        if blog_doc:
            review_data["blog"] = {
                "_id": str(blog_doc["_id"]),
                "name": blog_doc.get("name"),
                "short_desc": blog_doc.get("short_desc"),
            }
        else:
            review_data["blog"] = None
        review_data["course"] = None

    else:
        review_data["course"] = None
        review_data["blog"] = None

    return Review(**review_data)


async def get_review(
    db: Any,  # AsyncIOMotorDatabase
    review_id: str,
) -> Review:
    pipeline = [
        {"$match": {"_id": ObjectId(review_id)}},

        # Prepare object ids
        {
            "$addFields": {
                "user_obj_id": {"$toObjectId": "$user_id"},
                "replayer_obj_id": {
                    "$cond": {
                        "if": {"$ifNull": ["$replayer_id", False]},
                        "then": {"$toObjectId": "$replayer_id"},
                        "else": None
                    }
                },
                "type_obj_id": {"$toObjectId": "$type_id"}
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

        # Lookup replayer
        {
            "$lookup": {
                "from": "users",
                "localField": "replayer_obj_id",
                "foreignField": "_id",
                "as": "replayer"
            }
        },
        {"$unwind": {"path": "$replayer", "preserveNullAndEmptyArrays": True}},

        # Lookup course
        {
            "$lookup": {
                "from": "courses",
                "localField": "type_obj_id",
                "foreignField": "_id",
                "as": "course"
            }
        },
        {"$unwind": {"path": "$course", "preserveNullAndEmptyArrays": True}},

        # Lookup blog
        {
            "$lookup": {
                "from": "blogs",
                "localField": "type_obj_id",
                "foreignField": "_id",
                "as": "blog"
            }
        },
        {"$unwind": {"path": "$blog", "preserveNullAndEmptyArrays": True}},

        # Final projection
        {
            "$project": {
                "_id": 1,
                "type": 1,
                "type_id": 1,
                "user": 1,
                "replayer": 1,
                "rating": 1,
                "message": 1,
                "like_id": 1,
                "dislike_id": 1,
                "replay_message": 1,
                "replay_at": 1,
                "created_at": 1,
                "updated_at": 1,
                "course": {
                    "$cond": [
                        {"$eq": ["$type", "COURSE"]},
                        {
                            "_id": "$course._id",
                            "name": "$course.name",
                            "short_desc": "$course.short_desc",
                        },
                        None,
                    ]
                },
                "blog": {
                    "$cond": [
                        {"$eq": ["$type", "BLOG"]},
                        {
                            "_id": "$blog._id",
                            "name": "$blog.name",
                            "short_desc": "$blog.short_desc",
                        },
                        None,
                    ]
                },
            }
        }
    ]

    cursor = db.reviews.aggregate(pipeline)
    review_data = await cursor.to_list(length=1)

    if not review_data: 
        raise ReviewNotFound(f"Review with id {review_id} not found")

    review = review_data[0]

    # Convert ObjectIds to string
    if "_id" in review:
        review["_id"] = str(review["_id"])
    if review.get("user") and "_id" in review["user"]:
        review["user"]["_id"] = str(review["user"]["_id"])
    if review.get("replayer") and "_id" in review["replayer"]:
        review["replayer"]["_id"] = str(review["replayer"]["_id"])
    if review.get("course") and review["course"] and "_id" in review["course"]:
        review["course"]["_id"] = str(review["course"]["_id"])
    if review.get("blog") and review["blog"] and "_id" in review["blog"]:
        review["blog"]["_id"] = str(review["blog"]["_id"])

    return Review(**review)


async def delete_review(
    db: AsyncIOMotorDatabase, 
    review_id: str,
):
    result = await db.reviews.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 1:
        return True
    raise ReviewNotFound(f"Review with id {review_id} not found")


async def get_summary(
    db: AsyncIOMotorDatabase, 
    type: str, 
    type_id: str
):
    pipeline = [
        {"$match": {"type": type, "type_id": type_id}},
        {
            "$group": {
                "_id": None,
                "avg_rating": {"$avg": "$rating"},
                "total_reviews": {"$sum": 1},
                "five_star": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}},
                "four_star": {"$sum": {"$cond": [{"$eq": ["$rating", 4]}, 1, 0]}},
                "three_star": {"$sum": {"$cond": [{"$eq": ["$rating", 3]}, 1, 0]}},
                "two_star": {"$sum": {"$cond": [{"$eq": ["$rating", 2]}, 1, 0]}},
                "one_star": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "avg_rating": {"$toString": {"$round": ["$avg_rating", 1]}},
                "total_reviews": 1,
                "five_star": {
                    "$concat": [
                        {"$toString": {"$round": [
                            {"$multiply": [{"$divide": ["$five_star", "$total_reviews"]}, 100]}, 0
                        ]}},
                        "%"
                    ]
                },
                "four_star": {
                    "$concat": [
                        {"$toString": {"$round": [
                            {"$multiply": [{"$divide": ["$four_star", "$total_reviews"]}, 100]}, 0
                        ]}},
                        "%"
                    ]
                },
                "three_star": {
                    "$concat": [
                        {"$toString": {"$round": [
                            {"$multiply": [{"$divide": ["$three_star", "$total_reviews"]}, 100]}, 0
                        ]}},
                        "%"
                    ]
                },
                "two_star": {
                    "$concat": [
                        {"$toString": {"$round": [
                            {"$multiply": [{"$divide": ["$two_star", "$total_reviews"]}, 100]}, 0
                        ]}},
                        "%"
                    ]
                },
                "one_star": {
                    "$concat": [
                        {"$toString": {"$round": [
                            {"$multiply": [{"$divide": ["$one_star", "$total_reviews"]}, 100]}, 0
                        ]}},
                        "%"
                    ]
                },
            }
        }
    ]

    cursor = db["reviews"].aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        raise ReviewNotFound(f"No reviews found for type={type}, type_id={type_id}")

    return result[0]


async def replay_review(
    db: AsyncIOMotorDatabase, 
    review_id: str, 
    replayer_id: str, 
    review_replay: ReviewReplay,
) -> Review:
    update_data = {k: v for k, v in review_replay.dict().items() if v is not None}
    update_data["replayer_id"] = replayer_id
    update_data["replay_at"] = datetime.now()
    result = await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_review(db, review_id)
    raise ReviewNotFound(f"Review with id {review_id} not found")


async def react_review(
    db: AsyncIOMotorDatabase,
    review_id: str,
    reactor_id: str,
    react_as: str,
) -> Review:
    if react_as not in ["like", "dislike"]:
        raise ValueError("Invalid react_as. Must be 'like' or 'dislike'.")

    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise ReviewNotFound(f"Review with id {review_id} not found")

    like_ids = review.get("like_id", [])
    dislike_ids = review.get("dislike_id", [])

    update_query = {}

    if react_as == "like":
        if reactor_id in like_ids:
            # Already liked → remove it
            update_query["$pull"] = {"like_id": reactor_id}
        else:
            # Add like → also remove from dislike if present
            update_query["$addToSet"] = {"like_id": reactor_id}
            update_query.setdefault("$pull", {})["dislike_id"] = reactor_id

    elif react_as == "dislike":
        if reactor_id in dislike_ids:
            # Already disliked → remove it
            update_query["$pull"] = {"dislike_id": reactor_id}
        else:
            # Add dislike → also remove from like if present
            update_query["$addToSet"] = {"dislike_id": reactor_id}
            update_query.setdefault("$pull", {})["like_id"] = reactor_id

    result = await db.reviews.update_one(
        {"_id": ObjectId(review_id)},
        update_query
    )

    if result.modified_count == 1:
        return await get_review(db, review_id)

    return Review(**review)


