# app/services/engine_service.py

import os
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

_model: Optional[SentenceTransformer] = None


# ─────────────────────────────────────────────
# 🔥 LOAD MODEL (CALL ON STARTUP)
# ─────────────────────────────────────────────
def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )


# ─────────────────────────────────────────────
# 🧠 EMBEDDING
# ─────────────────────────────────────────────
def normalize_vector(v: List[float]) -> List[float]:
    v = np.array(v)
    norm = np.linalg.norm(v)
    return (v / norm).tolist() if norm > 0 else v.tolist()


def generate_embedding(text: str) -> Optional[List[float]]:
    if not text:
        return None
    if _model is None:
        raise RuntimeError("Embedding model not loaded. Call load_model().")
    vector = _model.encode(text)
    return normalize_vector(vector.tolist())


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2))


# ─────────────────────────────────────────────
# 🔤 FUZZY
# ─────────────────────────────────────────────
def fuzzy_score(text1: str, text2: str) -> float:
    return fuzz.ratio(text1.lower(), text2.lower()) / 100


# ─────────────────────────────────────────────
# 🧠 ADVANCED INTENT SCORING
# ─────────────────────────────────────────────
def score_intent(message_embedding, message_text, intent):
    embedding_scores = []

    for emb in intent.get("request_embeddings", []):
        embedding_scores.append(
            cosine_similarity(message_embedding, emb)
        )

    embedding_score = max(embedding_scores) if embedding_scores else 0

    fuzzy_scores = [
        fuzzy_score(message_text, req)
        for req in intent.get("requests", [])
    ]
    fuzzy_best = max(fuzzy_scores) if fuzzy_scores else 0

    priority_boost = intent.get("priority", 0) * 0.02

    pos = intent.get("positive_feedback", 0)
    neg = intent.get("negative_feedback", 0)
    feedback_boost = (pos / (pos + neg)) * 0.05 if (pos + neg) > 0 else 0

    final_score = (
        embedding_score * 0.6
        + fuzzy_best * 0.2
        + priority_boost
        + feedback_boost
    )

    return final_score