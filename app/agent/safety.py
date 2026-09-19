from enum import Enum
from typing import Dict, Any, Optional

class RiskLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"
    EXTERNAL = "EXTERNAL"

# Lightweight in-memory confirmation state mapping session_id to pending action
# In a real distributed app, use Redis or DB.
_PENDING_CONFIRMATIONS: Dict[str, Any] = {}

def set_pending_action(session_id: str, tool_name: str, arguments: Dict[str, Any], prompt: str):
    _PENDING_CONFIRMATIONS[session_id] = {
        "tool_name": tool_name,
        "arguments": arguments,
        "prompt": prompt
    }

def get_pending_action(session_id: str) -> Optional[Dict[str, Any]]:
    return _PENDING_CONFIRMATIONS.get(session_id)

def clear_pending_action(session_id: str):
    if session_id in _PENDING_CONFIRMATIONS:
        del _PENDING_CONFIRMATIONS[session_id]
