import re
import os
from pathlib import Path

# Common patterns for detection
SECRET_PATTERNS = [
    r"(?i)\bapi_key\b\s*[:=]\s*[\"']?[A-Za-z0-9_-]+[\"']?",
    r"(?i)\bbearer\b\s+[A-Za-z0-9_\-\.]+",
    r"(?i)\bpassword\b\s*(?:is|:|=)?\s*[\"']?[^\"'\s\.\,]+[\"']?",
    r"(?i)\bsecret\b\s*(?:is|:|=)?\s*[\"']?[^\"'\s\.\,]+[\"']?",
    r"(?i)\btoken\b\s*(?:is|:|=)?\s*[\"']?[^\"'\s\.\,]+[\"']?",
    r"(?i)private[-_]key\s*[:=]",
    r"sk-[a-zA-Z0-9]{20,}",
    r"AIza[0-9A-Za-z-_]{35}"
]

def detect_secrets(text: str) -> bool:
    """Returns True if a secret pattern is detected."""
    if not text:
        return False
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def validate_safe_path(target_path: str, base_dir: Path) -> bool:
    """
    Validates that target_path is within base_dir.
    Prevents path traversal attacks like ../../secret.txt.
    """
    try:
        resolved_target = Path(base_dir / target_path).resolve()
        resolved_base = base_dir.resolve()

        # is_relative_to is Python 3.9+
        return resolved_target.is_relative_to(resolved_base)
    except Exception:
        return False

def validate_safe_file_extension(filename: str, allowed: list[str] = None) -> bool:
    if allowed is None:
        allowed = [".txt", ".pdf", ".docx", ".md"]
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed
