# app/services/engine_service.py

import os
import numpy as np
from bson import ObjectId
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz
from typing import List, Optional
from app.core.config import settings

# ─────────────────────────────────────────────
# ⚙️ Environment Safety (Mac friendly)
# ─────────────────────────────────────────────
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

# ─────────────────────────────────────────────
# 🤖 Load Embedding Model (Singleton)
# ─────────────────────────────────────────────
_model = None


def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )


# ─────────────────────────────────────────────
# 🧠 Embedding Utilities
# ─────────────────────────────────────────────
def normalize_vector(v: List[float]) -> List[float]:
    v = np.array(v)
    norm = np.linalg.norm(v)
    return (v / norm).tolist() if norm > 0 else v.tolist()


def generate_embedding(text: str) -> Optional[List[float]]:
    if not text:
        return None

    if _model is None:
        raise RuntimeError("Embedding model not loaded")

    vector = _model.encode(text)
    return normalize_vector(vector.tolist())


# ─────────────────────────────────────────────
# 🔤 Fuzzy Matching
# ─────────────────────────────────────────────
def fuzzy_score(text1: str, text2: str) -> float:
    return fuzz.ratio(text1.lower(), text2.lower()) / 100


def best_fuzzy_match(message: str, examples: List[str]) -> float:
    scores = [fuzzy_score(message, ex) for ex in examples]
    return max(scores) if scores else 0.0


# ─────────────────────────────────────────────
# 💬 Context Handling
# ─────────────────────────────────────────────
async def get_recent_context(db, chat_id: str) -> str:
    cursor = db.conversations.find(
        {"chat_id": ObjectId(chat_id)}
    ).sort("created_at", -1).limit(settings.MAX_CONTEXT_MESSAGES)

    messages = await cursor.to_list(length=settings.MAX_CONTEXT_MESSAGES)

    return " ".join(
        m["content"]
        for m in reversed(messages)
        if m["sender_type"] == "user"
    )


# ─────────────────────────────────────────────
# 🎯 Intent Scoring Engine
# ─────────────────────────────────────────────
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def score_intent(
    message_embedding: List[float],
    intent: dict,
    PRIORITY_BOOST: float,
    FEEDBACK_BOOST: float
) -> float:

    best_score = 0.0

    # 🔥 Compare against ALL example embeddings
    for example_embedding in intent.get("example_embeddings", []):
        score = cosine_similarity(message_embedding, example_embedding)

        # Priority boost
        score += intent.get("priority", 0) * PRIORITY_BOOST

        # Feedback boost
        pos = intent.get("positive_feedback", 0)
        neg = intent.get("negative_feedback", 0)

        if pos + neg > 0:
            score += (pos / (pos + neg)) * FEEDBACK_BOOST

        best_score = max(best_score, score)

    return best_score