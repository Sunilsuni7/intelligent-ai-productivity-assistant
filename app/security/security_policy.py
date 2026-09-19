from typing import Dict, Any

def evaluate_tool_request(tool_name: str, risk_level: str, arguments: Dict[str, Any]) -> dict:
    """
    Evaluates whether a tool request is allowed and whether it requires confirmation.
    Returns: {"allowed": bool, "requires_confirmation": bool, "reason": str}
    """
    requires_conf = False

    # Base risk level checks
    if risk_level == "DESTRUCTIVE":
        requires_conf = True
    elif risk_level == "EXTERNAL":
        requires_conf = True
    elif risk_level == "WRITE":
        # Determine if bulk operation
        if _is_bulk_operation(tool_name, arguments):
            requires_conf = True

    return {
        "allowed": True,
        "requires_confirmation": requires_conf,
        "reason": "Evaluated by security policy"
    }

def _is_bulk_operation(tool_name: str, arguments: Dict[str, Any]) -> bool:
    # Example heuristic: if arguments contain a list of items > 5
    for k, v in arguments.items():
        if isinstance(v, list) and len(v) > 5:
            return True

    # Specific tool overrides
    if tool_name == "clear_memory":
        return True

    return False
