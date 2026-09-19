from typing import List, Dict, Any
from app.database.database import get_connection
from app.documents.embeddings import generate_embedding
from app.documents.vector_store import vector_store
import re

def retrieve_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # 1. Semantic Search
    query_emb = generate_embedding(query)
    semantic_results = vector_store.search(query_emb, top_k=top_k*2) # get more to rerank/merge

    # Extract chunk IDs from semantic search
    chunk_ids = [res["chunk_id"] for res in semantic_results]

    # 2. Fetch chunk metadata and text from DB
    connection = get_connection()
    cursor = connection.cursor()

    chunks_dict = {}
    if chunk_ids:
        placeholders = ','.join(['?'] * len(chunk_ids))
        cursor.execute(f'''
            SELECT c.id, c.text, c.page_number, d.filename
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.id IN ({placeholders})
        ''', chunk_ids)
        rows = cursor.fetchall()
        for row in rows:
            chunks_dict[row["id"]] = {
                "chunk_id": row["id"],
                "text": row["text"],
                "page_number": row["page_number"],
                "filename": row["filename"]
            }

    # Also do a quick keyword search across ALL chunks to simulate hybrid
    # In a real app we'd use FTS5 in SQLite, but we can just do a basic query or skip if semantic is good enough.
    # We will do a basic keyword match on the already retrieved chunks to boost their score.
    query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", query.lower()))

    final_results = []
    for sem_res in semantic_results:
        cid = sem_res["chunk_id"]
        if cid not in chunks_dict:
            continue

        chunk_data = chunks_dict[cid]
        text_lower = chunk_data["text"].lower()

        # Keyword boost
        keyword_matches = sum(1 for w in query_words if w in text_lower)
        keyword_score = keyword_matches * 0.05 # small boost

        final_score = sem_res["score"] + keyword_score

        # Only keep reasonable matches
        if final_score > 0.15: # threshold
            chunk_data["score"] = final_score
            final_results.append(chunk_data)

    connection.close()

    # Sort by final score
    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:top_k]
