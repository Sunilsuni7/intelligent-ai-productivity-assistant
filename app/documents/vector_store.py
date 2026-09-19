import os
import pickle
import numpy as np
from pathlib import Path
import threading

BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_FILE = BASE_DIR / "data" / "vector_index.pkl"

_STORE_LOCK = threading.Lock()

class VectorStore:
    def __init__(self):
        self.chunk_ids = []
        self.embeddings = None
        self.load()

    def load(self):
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        if INDEX_FILE.exists():
            with open(INDEX_FILE, 'rb') as f:
                data = pickle.load(f)
                self.chunk_ids = data.get("chunk_ids", [])
                self.embeddings = data.get("embeddings", None)
        else:
            self.chunk_ids = []
            self.embeddings = None

    def save(self):
        with open(INDEX_FILE, 'wb') as f:
            pickle.dump({
                "chunk_ids": self.chunk_ids,
                "embeddings": self.embeddings
            }, f)

    def add_embeddings(self, new_chunk_ids: list, new_embeddings: np.ndarray):
        with _STORE_LOCK:
            if not new_chunk_ids:
                return

            if self.embeddings is None:
                self.embeddings = new_embeddings
                self.chunk_ids = new_chunk_ids
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
                self.chunk_ids.extend(new_chunk_ids)
            self.save()

    def remove_embeddings_by_chunk_ids(self, ids_to_remove: set):
        with _STORE_LOCK:
            if self.embeddings is None or not self.chunk_ids:
                return

            keep_indices = [i for i, cid in enumerate(self.chunk_ids) if cid not in ids_to_remove]
            if len(keep_indices) == len(self.chunk_ids):
                return # nothing to remove

            if len(keep_indices) == 0:
                self.chunk_ids = []
                self.embeddings = None
            else:
                self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
                self.embeddings = self.embeddings[keep_indices]
            self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        if self.embeddings is None or len(self.chunk_ids) == 0:
            return []

        # Cosine similarity (assuming vectors are normalized, but we'll do dot product and normalize just in case)
        norm_query = np.linalg.norm(query_embedding)
        norm_db = np.linalg.norm(self.embeddings, axis=1)

        # Avoid division by zero
        norm_query = norm_query if norm_query > 0 else 1
        norm_db = np.where(norm_db > 0, norm_db, 1)

        similarities = np.dot(self.embeddings, query_embedding) / (norm_db * norm_query)

        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "chunk_id": self.chunk_ids[idx],
                "score": float(similarities[idx])
            })
        return results

# Global instance
vector_store = VectorStore()
