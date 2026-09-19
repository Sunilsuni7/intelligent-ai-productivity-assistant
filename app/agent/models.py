from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

class AgentRequest(BaseModel):
    message: str
    source: str = "text"
    session_id: str = "default"

class AgentPlan(BaseModel):
    intent: str = ""
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    requires_confirmation: bool = False

class ToolResult(BaseModel):
    success: bool
    tool_name: str
    data: Optional[Any] = None
    message: str
    error: Optional[str] = None
