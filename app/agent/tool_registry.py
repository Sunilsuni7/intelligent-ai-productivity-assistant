from typing import Callable, Dict, Any, List
from pydantic import BaseModel
from app.agent.safety import RiskLevel

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    risk_level: RiskLevel
    requires_confirmation: bool
    handler: Callable

TOOL_REGISTRY: Dict[str, ToolDefinition] = {}

def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    risk_level: RiskLevel,
    requires_confirmation: bool
):
    def decorator(handler: Callable):
        TOOL_REGISTRY[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            handler=handler
        )
        return handler
    return decorator

def get_tool(name: str) -> ToolDefinition:
    return TOOL_REGISTRY.get(name)

def list_registered_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "risk_level": t.risk_level.value,
            "requires_confirmation": t.requires_confirmation
        }
        for t in TOOL_REGISTRY.values()
    ]
