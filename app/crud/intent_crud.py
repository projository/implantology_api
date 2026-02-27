# app/crud/intent_crud.py

import math
import re
import pandas as pd

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from collections import Counter
from io import BytesIO

from app.models.intent import Intent, IntentCreate, IntentUpdate


class IntentNotFound(Exception):
    pass


# ───────────────── CRUD ─────────────────

async def create_intent(db: AsyncIOMotorDatabase, intent_create: IntentCreate) -> Intent:
    data = intent_create.dict()
    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()
    data["match_count"] = 0
    data["positive_feedback"] = 0
    data["negative_feedback"] = 0
    data["user_weights"] = {}

    result = await db.intents.insert_one(data)
    data["_id"] = str(result.inserted_id)

    return Intent(**data)


async def get_intent(db: AsyncIOMotorDatabase, intent_id: str) -> Intent:
    intent = await db.intents.find_one({"_id": ObjectId(intent_id)})
    if not intent:
        raise IntentNotFound("Intent not found")

    intent["_id"] = str(intent["_id"])
    return Intent(**intent)


async def update_intent(
    db: AsyncIOMotorDatabase,
    intent_id: str,
    intent_update: IntentUpdate,
) -> Intent:

    update_data = {k: v for k, v in intent_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()

    result = await db.intents.update_one(
        {"_id": ObjectId(intent_id)},
        {"$set": update_data},
    )

    if result.modified_count != 1:
        raise IntentNotFound("Intent not found")

    return await get_intent(db, intent_id)


async def delete_intent(db: AsyncIOMotorDatabase, intent_id: str):
    result = await db.intents.delete_one({"_id": ObjectId(intent_id)})
    if result.deleted_count != 1:
        raise IntentNotFound("Intent not found")
    return True


async def delete_all_intents(db: AsyncIOMotorDatabase) -> int:
    result = await db.intents.delete_many({})
    return result.deleted_count

# ───────────────── LIST WITH PAGINATION ─────────────────

async def get_intents(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None,
) -> Dict[str, Any]:

    skip = (page - 1) * per_page
    query = {}

    if search_key:
        query = {
            "intent": {"$regex": search_key, "$options": "i"}
        }

    cursor = (
        db.intents
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(per_page)
    )

    items = await cursor.to_list(length=per_page)

    for item in items:
        item["_id"] = str(item["_id"])

    total = await db.intents.count_documents(query)

    return {
        "data": [Intent(**item).dict() for item in items],
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }


# ───────────────── CHAT MATCHING LOGIC ─────────────────

STOPWORDS = {"the", "a", "an"}
CONFIDENCE_THRESHOLD = 0.3


def _normalize(text: str):
    text = text.lower().strip()
    return re.sub(r"[^\w\s]", "", text)


def _tokenize(text: str):
    return [w for w in text.split() if w not in STOPWORDS]


def _cosine_similarity(a: Counter, b: Counter):
    intersection = set(a.keys()) & set(b.keys())
    dot = sum(a[x] * b[x] for x in intersection)

    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))

    if not norm_a or not norm_b:
        return 0.0

    return dot / (norm_a * norm_b)


async def generate_reply(
    db: AsyncIOMotorDatabase,
    message: str,
) -> Dict[str, Any]:

    normalized = _normalize(message)
    words = _tokenize(normalized)
    message_vector = Counter(words)

    intents_cursor = db.intents.find({"is_active": True})
    intents = await intents_cursor.to_list(length=None)

    best_intent = None
    best_score = 0

    for intent in intents:
        examples_text = " ".join(intent.get("examples", []) + [intent["intent"]])
        intent_words = _tokenize(_normalize(examples_text))
        intent_vector = Counter(intent_words)

        cosine = _cosine_similarity(message_vector, intent_vector)
        score = cosine * 5

        for kw in intent.get("keywords", []):
            if kw["word"] in words:
                score += kw["weight"] * 2

        score += intent.get("priority", 0) * 0.5
        score += intent.get("match_count", 0) * 0.05

        if score > best_score:
            best_score = score
            best_intent = intent

    confidence = min(best_score / 10, 1.0)

    if best_intent and confidence >= CONFIDENCE_THRESHOLD:
        await db.intents.update_one(
            {"_id": best_intent["_id"]},
            {
                "$inc": {"match_count": 1},
                "$set": {"last_matched": datetime.now()},
            },
        )

        return {
            "message": best_intent["response"],
            "intent": best_intent["intent"],
            "confidence": round(confidence, 3),
            "fallback": False,
        }

    fallback = await db.intents.find_one({"is_fallback": True})

    return {
        "message": fallback["response"] if fallback else "I'm still learning.",
        "intent": None,
        "confidence": 0.0,
        "fallback": True,
    }


async def upload_intents(
    db: AsyncIOMotorDatabase,
    file_bytes: bytes
) -> Dict[str, Any]:

    df = pd.read_excel(BytesIO(file_bytes))

    inserted = []
    errors = []

    for index, row in df.iterrows():
        try:
            # ─── Parse examples ───
            examples = []
            if pd.notna(row.get("examples")):
                examples = [
                    e.strip()
                    for e in str(row["examples"]).split(",")
                    if e.strip()
                ]

            # ─── Parse keywords ───
            keywords = []
            if pd.notna(row.get("keywords")):
                for item in str(row["keywords"]).split(","):
                    if ":" in item:
                        word, weight = item.split(":")
                        keywords.append({
                            "word": word.strip(),
                            "weight": int(weight.strip())
                        })

            # ─── Build Intent Document ───
            intent_data = {
                "intent": row["intent"],
                "examples": examples,
                "keywords": keywords,
                "response": row["response"],
                "priority": int(row.get("priority", 0)),
                "is_active": bool(row.get("is_active", True)),
                "is_fallback": bool(row.get("is_fallback", False)),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "match_count": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "user_weights": {}
            }

            # Optional: Prevent duplicate intent names
            existing = await db.intents.find_one({"intent": intent_data["intent"]})
            if existing:
                continue

            await db.intents.insert_one(intent_data)
            inserted.append(intent_data["intent"])

        except Exception as e:
            errors.append({
                "row": index + 1,
                "error": str(e)
            })

    return {
        "inserted_count": len(inserted),
        "inserted_intents": inserted,
        "errors": errors
    }