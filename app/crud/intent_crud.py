# app/crud/intent_crud.py

import math
import re
import random
import pandas as pd

from rapidfuzz import fuzz

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
CONFIDENCE_THRESHOLD = 0.45

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
    session_id: Optional[str] = None,
) -> Dict[str, Any]:

    normalized = _normalize(message)
    words = _tokenize(normalized)
    message_vector = Counter(words)

    session = None
    if session_id:
        session = await db.sessions.find_one({"session_id": session_id})

    intents = await db.intents.find({"is_active": True}).to_list(None)

    best_intent = None
    best_score = 0.0

    for intent in intents:

        examples_text = " ".join(
            intent.get("examples", []) + [intent["intent"]]
        )

        intent_words = _tokenize(_normalize(examples_text))
        intent_vector = Counter(intent_words)

        # 1️⃣ Cosine Similarity
        cosine = _cosine_similarity(message_vector, intent_vector)

        # 2️⃣ Fuzzy Matching
        fuzzy_score = fuzz.partial_ratio(
            normalized,
            _normalize(examples_text)
        ) / 100

        # 3️⃣ Keyword Weighted Score (Normalized)
        keyword_score = 0
        total_weight = 0

        for kw in intent.get("keywords", []):
            total_weight += kw.get("weight", 1)
            if kw["word"].lower() in words:
                keyword_score += kw.get("weight", 1)

        if total_weight > 0:
            keyword_score = keyword_score / total_weight
        else:
            keyword_score = 0

        # 4️⃣ Feedback Learning Boost
        positive = intent.get("positive_feedback", 0)
        negative = intent.get("negative_feedback", 0)

        feedback_score = 0
        if positive + negative > 0:
            feedback_score = positive / (positive + negative)

        # 5️⃣ Priority Normalized
        priority = intent.get("priority", 0)
        priority_score = min(priority / 10, 1)

        # 🔥 Final Weighted Score (0–1 range)
        score = (
            cosine * 0.35 +
            fuzzy_score * 0.30 +
            keyword_score * 0.20 +
            feedback_score * 0.10 +
            priority_score * 0.05
        )

        # Context Boost
        if session and len(words) <= 2:
            if session.get("last_intent") == intent["intent"]:
                score += 0.1

        if score > best_score:
            best_score = score
            best_intent = intent

    confidence = round(best_score, 3)

    if best_intent and confidence >= CONFIDENCE_THRESHOLD:

        responses = best_intent.get("responses", [])
        reply = random.choice(responses) if responses else "Okay."

        await db.intents.update_one(
            {"_id": best_intent["_id"]},
            {
                "$inc": {"match_count": 1},
                "$set": {"last_matched": datetime.now()},
            },
        )

        if session_id:
            await db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "last_intent": best_intent["intent"],
                        "last_message": message,
                        "updated_at": datetime.now(),
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(),
                        "context": {},
                    },
                },
                upsert=True,
            )

        return {
            "message": reply,
            "intent": best_intent["intent"],
            "confidence": confidence,
            "fallback": False,
        }

    return {
        "message": random.choice([
            "Hmm 🤔 I didn’t quite understand that.",
            "Could you rephrase that?",
            "I'm not sure I understood. Can you try again?"
        ]),
        "intent": None,
        "confidence": confidence,
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
                    for e in str(row["examples"]).split("|")
                    if e.strip()
                ]

            # ─── Parse keywords ───
            keywords = []
            if pd.notna(row.get("keywords")):
                for item in str(row["keywords"]).split("|"):
                    if ":" in item:
                        word, weight = item.split(":")
                        keywords.append({
                            "word": word.strip(),
                            "weight": int(weight.strip())
                        })

            # ─── Parse responses ───
            responses = []
            if pd.notna(row.get("responses")):
                responses = [
                    r.strip()
                    for r in str(row["responses"]).split("|")
                    if r.strip()
                ]

            # ─── Build Intent Document ───
            intent_data = {
                "intent": row["intent"],
                "examples": examples,
                "keywords": keywords,
                "response": responses,
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