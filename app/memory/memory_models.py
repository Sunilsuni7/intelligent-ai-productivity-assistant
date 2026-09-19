from typing import Optional
from pydantic import BaseModel

class MemoryRecord(BaseModel):
    id: Optional[int] = None
    content: str
    category: Optional[str] = None
    source: str = 'explicit'
    importance: str = 'medium'
    confidence: float = 1.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_used_at: Optional[str] = None
    active: int = 1
