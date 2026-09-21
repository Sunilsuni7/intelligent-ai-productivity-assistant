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

class ActionPlan(BaseModel):
    type: str = Field(..., description="'tool' or 'conversation'")
    tool_name: str = Field(..., description="The name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict)

class AgentDecision(BaseModel):
    classification: str = Field(..., description="'CONVERSATION', 'TOOL ACTION', or 'MULTI-STEP ACTION'")
    plans: List[ActionPlan] = Field(default_factory=list)
    response: Optional[str] = Field(None, description="Direct response if CONVERSATION")

class StepResult(BaseModel):
    step_number: int
    tool_name: str
    success: bool
    message: str
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    overall_success: bool
    completed_steps: int
    failed_step: Optional[int] = None
    step_results: List[StepResult] = Field(default_factory=list)
