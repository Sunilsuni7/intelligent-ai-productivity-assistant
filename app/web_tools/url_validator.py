from urllib.parse import urlparse

OFFICIAL_ALLOWLIST = {
    "python": "https://www.python.org/",
    "python_docs": "https://docs.python.org/",
    "github": "https://github.com/",
    "fastapi": "https://fastapi.tiangolo.com/",
    "streamlit": "https://streamlit.io/",
    "youtube": "https://www.youtube.com/"
}

def validate_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # 1. Scheme MUST be http or https
        if parsed.scheme not in ["http", "https"]:
            return False

        # 2. Prevent credentials in URL (e.g. http://user:pass@host/)
        if "@" in parsed.netloc:
            # We reject any basic auth embedded in URLs for safety
            return False

        # 3. Must have a hostname
        if not parsed.hostname:
            return False

        # 4. Reject localhost/127.0.0.1 to prevent SSRF against local dev,
        # unless it's explicitly allowed (for production tools, usually reject)
        # But we'll just check for basic valid schemes per instructions.
        # "Prevent local file access" -> handled by rejecting file:// scheme

        return True
    except Exception:
        return False

def get_official_url(name: str) -> str:
    """Returns the official URL if it exists in the allowlist, otherwise empty string."""
    key = name.lower().strip()
    return OFFICIAL_ALLOWLIST.get(key, "")
