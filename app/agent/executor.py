from typing import Dict, Any
import jsonschema
from app.agent.models import ToolResult
from app.agent.tool_registry import get_tool
from app.agent.safety import RiskLevel, set_pending_action
from app.security.security_policy import evaluate_tool_request
from app.security.audit_logger import log_audit_event
from app.security.security_models import AuditEvent
import logging

def execute_tool(tool_name: str, arguments: Dict[str, Any], session_id: str = "default", prompt: str = "") -> ToolResult:
    tool_def = get_tool(tool_name)
    if not tool_def:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="Tool not found.",
            error=f"Tool '{tool_name}' is not registered."
        )

    # 1. Security Policy check
    policy = evaluate_tool_request(tool_name, tool_def.risk_level, arguments)
    if not policy["allowed"]:
        log_audit_event(session_id, AuditEvent(action="tool_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="BLOCKED", reason=policy["reason"], arguments=arguments))
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="Action blocked by security policy.",
            error=policy["reason"]
        )

    # 2. Validate Arguments
    try:
        jsonschema.validate(instance=arguments, schema=tool_def.input_schema)
    except jsonschema.exceptions.ValidationError as e:
        log_audit_event(session_id, AuditEvent(action="tool_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="ERROR", reason="invalid_arguments", arguments=arguments))
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="Invalid arguments provided.",
            error=str(e)
        )

    # 3. Safety Check (DESTRUCTIVE, EXTERNAL, BULK actions require confirmation)
    if tool_def.requires_confirmation or policy["requires_confirmation"]:
        set_pending_action(session_id, tool_name, arguments, prompt)
        log_audit_event(session_id, AuditEvent(action="tool_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="CONFIRMATION_REQUIRED", reason=policy["reason"], arguments=arguments))
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message=f"Confirmation required. This action '{tool_name}' has risk level {tool_def.risk_level.upper()}. Do you want to continue?",
            data={"requires_confirmation": True}
        )

        # 4. Execute handler
    try:
        import inspect
        sig = inspect.signature(tool_def.handler)
        exec_args = dict(arguments)
        if "session_id" in sig.parameters:
            exec_args["session_id"] = session_id

        result_data = tool_def.handler(**exec_args)
        log_audit_event(session_id, AuditEvent(action="tool_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="SUCCESS", reason="execution_complete", arguments=arguments))
        return ToolResult(
            success=True,
            tool_name=tool_name,
            data=result_data,
            message=f"Successfully executed {tool_name}."
        )
    except Exception as e:
        logging.error(f"Error executing {tool_name}: {e}")
        log_audit_event(session_id, AuditEvent(action="tool_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="ERROR", reason=str(e), arguments=arguments))
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="An error occurred during tool execution.",
            error=str(e)
        )

def execute_confirmed_action(session_id: str, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
    tool_def = get_tool(tool_name)
    if not tool_def:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="Tool not found.",
            error="Tool not registered."
        )

    try:
        import inspect
        sig = inspect.signature(tool_def.handler)
        exec_args = dict(arguments)
        if "session_id" in sig.parameters:
            exec_args["session_id"] = session_id

        result_data = tool_def.handler(**exec_args)
        log_audit_event(session_id, AuditEvent(action="confirmed_execution", tool_name=tool_name, risk_level=tool_def.risk_level, result="SUCCESS", reason="execution_complete", arguments=arguments))
        return ToolResult(
            success=True,
            tool_name=tool_name,
            data=result_data,
            message=f"Successfully executed {tool_name} after confirmation."
        )
    except Exception as e:
        logging.error(f"Error executing {tool_name} after confirmation: {e}")
        return ToolResult(
            success=False,
            tool_name=tool_name,
            message="An error occurred during tool execution.",
            error=str(e)
        )

