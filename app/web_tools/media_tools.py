from urllib.parse import quote_plus
from app.web_tools.url_validator import get_official_url

def construct_youtube_search_url(query: str) -> str:
    """
    Constructs a safe YouTube search URL.
    """
    if not query:
        return get_official_url("youtube")

    encoded_query = quote_plus(query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"
