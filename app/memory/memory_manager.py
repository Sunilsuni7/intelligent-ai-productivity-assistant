import re
from typing import List, Dict, Any
from app.database.database import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo

SENSITIVE_PATTERNS = [
    r'\b(password|passwd|pwd)\b\s*[:=]\s*\S+',
    r'\b(api_key|apikey|secret|token)\b\s*[:=]\s*\S+',
    r'\bssn\b',
    r'\bcredit card\b',
    r'\baccount number\b'
]

def contains_sensitive_info(text: str) -> bool:
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False

def _get_ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

def add_memory(session_id, content: str, category: str = "preference", importance: str = "medium", source: str = "explicit") -> Dict[str, Any]:
    if contains_sensitive_info(content):
        return {"success": False, "message": "Refused to store sensitive information."}

    conn = get_connection()
    cursor = conn.cursor()

    # Simple Deduplication / Conflict check using exact or highly similar content
    # For a real system we'd use embeddings. We'll use basic word overlap here since embeddings failed.
    cursor.execute("SELECT id, content FROM memories WHERE active = 1")
    existing = cursor.fetchall()

    query_words = set(re.findall(r'\b\w+\b', content.lower()))

    for row in existing:
        existing_words = set(re.findall(r'\b\w+\b', row['content'].lower()))
        if not query_words or not existing_words:
            continue

        intersection = query_words.intersection(existing_words)
        overlap = len(intersection) / max(len(query_words), len(existing_words))

        # High overlap -> deduplicate or supersede
        if overlap > 0.8:
            # Supersede existing memory
            cursor.execute("UPDATE memories SET active = 0, updated_at = ? WHERE id = ?", (_get_ist_now(), row['id']))
            break # Just supersede the closest match

    now = _get_ist_now()
    cursor.execute('''
        INSERT INTO memories (content, category, source, importance, created_at, updated_at, active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (content, category, source, importance, now, now))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Memory saved."}

def list_memories() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, category, importance, last_used_at, active FROM memories WHERE active = 1 ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def deactivate_memory(session_id, content_query: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, content FROM memories WHERE active = 1")
    existing = cursor.fetchall()

    query_words = set(re.findall(r'\b\w+\b', content_query.lower()))

    best_match_id = None
    best_overlap = 0

    for row in existing:
        existing_words = set(re.findall(r'\b\w+\b', row['content'].lower()))
        if not query_words or not existing_words:
            continue

        intersection = query_words.intersection(existing_words)
        overlap = len(intersection) / max(len(query_words), len(existing_words))

        if overlap > best_overlap:
            best_overlap = overlap
            best_match_id = row['id']

    if best_match_id and best_overlap > 0.3:
        cursor.execute("UPDATE memories SET active = 0, updated_at = ? WHERE id = ?", (_get_ist_now(), best_match_id))
        conn.commit()
        conn.close()
        return {"success": True, "message": "I've removed that memory."}

    conn.close()
    return {"success": False, "message": "Could not find a matching memory to remove."}
