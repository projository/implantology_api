# app/crud/intent_crud.py

import math
import pandas as pd
import numpy as np

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from io import BytesIO
from sklearn.metrics.pairwise import cosine_similarity


from app.core.config import settings
from app.models.intent import Intent, IntentCreate, IntentUpdate
from app.services.engine_service import fuzzy_score, generate_embedding, get_recent_context, normalize_vector


class IntentNotFound(Exception):
    pass


def parse_bool(value, default=True):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes"]
    if isinstance(value, int):
        return value == 1
    return default


async def create_intent(db: AsyncIOMotorDatabase, intent_create: IntentCreate) -> Intent:

    intent_name = intent_create.intent.strip()

    existing = await db.intents.find_one({"intent": intent_name})
    if existing:
        raise ValueError("Intent already exists")

    request_embeddings = [
        generate_embedding(request)
        for request in intent_create.requests
    ]

    data = intent_create.dict()
    data["intent"] = intent_name
    data["request_embeddings"] = request_embeddings
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    data["match_count"] = 0
    data["positive_feedback"] = 0
    data["negative_feedback"] = 0

    result = await db.intents.insert_one(data)
    data["_id"] = str(result.inserted_id)

    return Intent(**data)


async def get_intent(db: AsyncIOMotorDatabase, intent_id: str) -> Intent:

    try:
        obj_id = ObjectId(intent_id)
    except Exception:
        raise IntentNotFound("Invalid intent ID")

    intent = await db.intents.find_one({"_id": obj_id})

    if not intent:
        raise IntentNotFound("Intent not found")

    intent["_id"] = str(intent["_id"])
    return Intent(**intent)


async def get_intents(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None,
) -> Dict[str, Any]:

    skip = (page - 1) * per_page
    query = {}

    if search_key:
        query["intent"] = {"$regex": search_key, "$options": "i"}

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


async def update_intent(
    db: AsyncIOMotorDatabase,
    intent_id: str,
    intent_update: IntentUpdate,
) -> Intent:

    update_data = {k: v for k, v in intent_update.dict().items() if v is not None}

    if "requests" in update_data:
        update_data["request_embeddings"] = [
            generate_embedding(request)
            for request in update_data["requests"]
        ]

    update_data["updated_at"] = datetime.utcnow()

    result = await db.intents.update_one(
        {"_id": ObjectId(intent_id)},
        {"$set": update_data},
    )

    if result.matched_count != 1:
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


async def upload_intents(
    db: AsyncIOMotorDatabase,
    file_bytes: bytes
) -> Dict[str, Any]:

    df = pd.read_excel(BytesIO(file_bytes))

    if "intent" not in df.columns:
        raise ValueError("Excel must contain 'intent' column")

    inserted = []
    errors = []

    for index, row in df.iterrows():
        try:

            intent_name = str(row["intent"]).strip()
            if not intent_name:
                continue

            requests = str(row.get("requests", "")).split("|")
            responses = str(row.get("responses", "")).split("|")

            requests = [e.strip() for e in requests if e.strip()]
            responses = [r.strip() for r in responses if r.strip()]

            request_embeddings = [
                generate_embedding(request)
                for request in requests
            ]

            intent_data = {
                "intent": intent_name,
                "requests": requests,
                "responses": responses,
                "request_embeddings": request_embeddings,
                "priority": int(row.get("priority", 0)),
                "is_active": parse_bool(row.get("is_active", True)),
                "is_fallback": parse_bool(row.get("is_fallback", False), False),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "match_count": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
            }

            existing = await db.intents.find_one({"intent": intent_name})
            if existing:
                continue

            await db.intents.insert_one(intent_data)
            inserted.append(intent_name)

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


async def generate_reply(
    db,
    message: str,
    chat_id: str
) -> Dict[str, Any]:

    message_clean = message.lower().strip()

    # ─────────────────────────────
    # 1️⃣ EXACT MATCH (FAST PATH)
    # ─────────────────────────────
    rule_intent = await db.intents.find_one({
        "is_active": True,
        "requests": {"$in": [message_clean]}
    })

    if rule_intent:
        reply = np.random.choice(rule_intent["responses"])
        return {
            "message": reply,
            "intent_id": str(rule_intent["_id"]),
            "confidence": 0.99,
            "decision": "bot"
        }

    # ─────────────────────────────
    # 2️⃣ FUZZY MATCH (TYPO SAFE)
    # ─────────────────────────────
    intents = await db.intents.find({"is_active": True}).to_list(None)

    best_fuzzy_score = 0
    best_fuzzy_intent = None

    for intent in intents:
        for ex in intent.get("requests", []):
            score = fuzzy_score(message_clean, ex)
            if score > best_fuzzy_score:
                best_fuzzy_score = score
                best_fuzzy_intent = intent

    if best_fuzzy_intent and best_fuzzy_score >= settings.FUZZY_THRESHOLD:
        reply = np.random.choice(best_fuzzy_intent["responses"])
        return {
            "message": reply,
            "intent_id": str(best_fuzzy_intent["_id"]),
            "confidence": round(best_fuzzy_score, 3),
            "decision": "bot"
        }

    # ─────────────────────────────
    # 3️⃣ CONTEXT-AWARE EMBEDDING MATCH
    # ─────────────────────────────
    context_text = await get_recent_context(db, chat_id)
    combined_input = f"{context_text} {message}".strip()

    user_embedding = normalize_vector(generate_embedding(combined_input))

    best_score = 0
    best_intent = None

    for intent in intents:
        for ex_embedding in intent.get("request_embeddings", []):
            similarity = cosine_similarity(
                [user_embedding],
                [normalize_vector(ex_embedding)]
            )[0][0]

            # context boost
            if context_text:
                similarity += settings.CONTEXT_BOOST

            if similarity > best_score:
                best_score = similarity
                best_intent = intent

    confidence = round(float(best_score), 3)

    # ─────────────────────────────
    # DECISION LOGIC
    # ─────────────────────────────
    if best_intent and confidence >= settings.CONFIDENCE_HIGH:
        reply = np.random.choice(best_intent["responses"])
        return {
            "message": reply,
            "intent_id": str(best_intent["_id"]),
            "confidence": confidence,
            "decision": "bot"
        }

    if best_intent and confidence >= settings.CONFIDENCE_LOW:
        return {
            "message": f"Did you mean '{best_intent['intent']}'?",
            "intent_id": str(best_intent["_id"]),
            "confidence": confidence,
            "decision": "clarification"
        }

    return {
        "message": "Your message has been forwarded to a human agent.",
        "intent_id": None,
        "confidence": confidence,
        "decision": "escalate"
    }