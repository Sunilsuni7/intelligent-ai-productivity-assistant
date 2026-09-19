import os
from urllib.parse import quote_plus
from datetime import datetime
from zoneinfo import ZoneInfo
from app.web_tools.web_models import WebSearchRequest, WebSearchResponse

def perform_web_search(request: WebSearchRequest) -> WebSearchResponse:
    provider = os.getenv("WEB_SEARCH_PROVIDER", "").strip().lower()

    # Check for credentials inside query to filter out
    low_query = request.query.lower()
    if "password" in low_query or "api_key" in low_query or "secret" in low_query:
        return WebSearchResponse(
            query=request.query,
            success=False,
            message="Search rejected: Query appears to contain sensitive credential information.",
            provider="none"
        )

    if not request.query.strip():
        return WebSearchResponse(
            query=request.query,
            success=False,
            message="Search rejected: Empty query.",
            provider="none"
        )

    # In a real implementation we would call Google/DDG APIs here.
    # But since we are restricted to no paid APIs and avoiding scraping,
    # we provide the honest fallback.

    encoded_query = quote_plus(request.query)
    fallback_url = f"https://duckduckgo.com/?q={encoded_query}"

    return WebSearchResponse(
        query=request.query,
        success=False,
        provider="fallback",
        message=f"Structured web search is unavailable. You can open a safe search page instead: {fallback_url}"
    )
