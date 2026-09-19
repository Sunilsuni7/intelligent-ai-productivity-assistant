from typing import List, Optional
from pydantic import BaseModel

class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = "web"
    retrieved_at: Optional[str] = None

class WebSearchResponse(BaseModel):
    query: str
    results: List[WebSearchResult] = []
    provider: str = "none"
    success: bool = False
    message: str = ""

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    safe_search: bool = True
