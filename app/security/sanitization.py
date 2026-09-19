from app.security.validators import SECRET_PATTERNS
import re
import copy

def sanitize_text(text: str) -> str:
    """Masks detected secrets in text."""
    if not text:
        return text
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED_SECRET]", sanitized)
    return sanitized

def sanitize_dict(d: dict) -> dict:
    """Masks detected secrets in a dictionary of arguments."""
    if not d:
        return {}
    sanitized = copy.deepcopy(d)
    for k, v in sanitized.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_text(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
    return sanitized
