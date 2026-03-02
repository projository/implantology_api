# app/crud/intent_crud.py

import math
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from app.services.embedding_service import generate_embedding
from app.services.entity_service import extract_entities
from app.services.flow_service import handle_multi_turn

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from io import BytesIO

from app.services.embedding_service import generate_embedding
from app.models.intent import Intent, IntentCreate, IntentUpdate


class IntentNotFound(Exception):
    pass


# ───────────────── CRUD ─────────────────

async def create_intent(db: AsyncIOMotorDatabase, intent_create: IntentCreate) -> Intent:
    examples_text = " ".join(intent_create.examples)

    embedding = generate_embedding(examples_text)

    data = intent_create.dict()
    data["embedding"] = embedding
    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()

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

CONFIDENCE_THRESHOLD = 0.50

async def generate_reply(
    db: AsyncIOMotorDatabase,
    message: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:

    user_embedding = generate_embedding(message)

    session = None
    if session_id:
        session = await db.sessions.find_one({"session_id": session_id})

    intents = await db.intents.find({"is_active": True}).to_list(None)

    best_intent = None
    best_score = 0

    for intent in intents:

        if not intent.get("embedding"):
            continue

        score = cosine_similarity(
            [user_embedding],
            [intent["embedding"]]
        )[0][0]

        # feedback boost
        pos = intent.get("positive_feedback", 0)
        neg = intent.get("negative_feedback", 0)

        if pos + neg > 0:
            score += (pos / (pos + neg)) * 0.1

        if score > best_score:
            best_score = score
            best_intent = intent

    confidence = round(float(best_score), 3)

    if best_intent and confidence >= CONFIDENCE_THRESHOLD:

        entities = extract_entities(message)

        # update session
        if session_id:
            await db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "last_intent": best_intent["intent"],
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(),
                        "collected_entities": {}
                    }
                },
                upsert=True
            )

        # multi-turn
        if session:
            session["collected_entities"].update(entities)
            next_question = handle_multi_turn(best_intent, session)
            if next_question:
                return {
                    "message": next_question,
                    "intent": best_intent["intent"],
                    "confidence": confidence,
                    "entities": session["collected_entities"],
                    "fallback": False
                }

        reply = np.random.choice(best_intent.get("responses", ["Okay."]))

        return {
            "message": reply,
            "intent": best_intent["intent"],
            "confidence": confidence,
            "entities": entities,
            "fallback": False,
        }

    return {
        "message": "I'm not sure I understood that. Could you rephrase?",
        "intent": None,
        "confidence": confidence,
        "entities": None,
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