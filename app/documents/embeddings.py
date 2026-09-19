import os
import threading
from typing import List
import numpy as np

# A global lock and instance to ensure we only load the model once
_MODEL_LOCK = threading.Lock()
_EMBEDDING_MODEL = None

def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        with _MODEL_LOCK:
            if _EMBEDDING_MODEL is None:
                from sentence_transformers import SentenceTransformer
                # Using a lightweight model suitable for CPU
                _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return _EMBEDDING_MODEL

def generate_embeddings(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.array([])
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings

def generate_embedding(text: str) -> np.ndarray:
    return generate_embeddings([text])[0]
