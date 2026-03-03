# app/services/embedding_service.py

import os
from sentence_transformers import SentenceTransformer

# Prevent tokenizer multiprocessing issues
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

_model = None


def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"  # safer for Mac dev
        )


def generate_embedding(text: str):
    if not text:
        return None

    if _model is None:
        raise RuntimeError("Embedding model not loaded")

    return _model.encode(text).tolist()