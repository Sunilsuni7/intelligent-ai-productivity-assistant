import re
from typing import List, Dict, Any
from app.database.database import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo

def _get_ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

def retrieve_relevant_memories(query: str, session_id: str = "default", top_k: int = 3) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, category, importance, created_at, last_used_at FROM memories WHERE session_id = ? AND active = 1", (session_id,))
    memories = [dict(r) for r in cursor.fetchall()]

    if not memories:
        conn.close()
        return []

    query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))

    scored_memories = []

    for mem in memories:
        mem_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', mem['content'].lower()))

        # 1. Relevance
        intersection = query_words.intersection(mem_words)
        relevance_score = len(intersection) / max(len(query_words), 1)

        # Base relevancy (give a slight boost to everything so nothing is totally 0 if it's general context)
        score = relevance_score * 0.8 + 0.1

        # 2. Importance
        importance = mem.get("importance", "medium").lower()
        if importance == "high":
            score *= 1.2
        elif importance == "low":
            score *= 0.8

        # 3. Recency (very basic)
        # Not fully implemented to avoid complex date math for now, but placeholder is here

        scored_memories.append((score, mem))

    scored_memories.sort(key=lambda x: x[0], reverse=True)

    # Take top k
    top_memories = [m[1] for m in scored_memories if m[0] > 0.1][:top_k]

    # Update last_used_at for retrieved ones
    now = _get_ist_now()
    for mem in top_memories:
        cursor.execute("UPDATE memories SET last_used_at = ? WHERE id = ?", (now, mem['id']))

    conn.commit()
    conn.close()

    return top_memories
