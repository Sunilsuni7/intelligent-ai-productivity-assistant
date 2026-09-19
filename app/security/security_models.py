from pydantic import BaseModel
from typing import Optional, Dict, Any

class AuditEvent(BaseModel):
    action: str
    tool_name: str
    risk_level: str
    result: str # SUCCESS, BLOCKED, CONFIRMATION_REQUIRED, ERROR
    reason: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None

class SecurityCheckResult(BaseModel):
    is_safe: bool
    reason: Optional[str] = None
    sanitized_input: Optional[str] = None
