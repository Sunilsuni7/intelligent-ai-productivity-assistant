import pytest
from app.agent.tool_registry import get_tool, list_registered_tools
from app.agent.safety import RiskLevel, set_pending_action, get_pending_action, clear_pending_action
from app.agent.executor import execute_tool, execute_confirmed_action
from app.agent.models import AgentRequest
from app.agent.agent import handle_request
from unittest.mock import patch
from app.database.database import create_tables

@pytest.fixture(autouse=True)
def setup_test_db():
    create_tables()

def test_registry_tool_lookup():
    tool = get_tool("create_task")
    assert tool is not None
    assert tool.name == "create_task"
    assert tool.risk_level == RiskLevel.WRITE
    assert tool.requires_confirmation is False

def test_registry_unknown_tool():
    tool = get_tool("nonexistent_tool")
    assert tool is None

def test_validation_missing_arguments():
    # create_task requires 'title' and 'priority'
    result = execute_tool("create_task", {"title": "Missing Priority"})
    assert result.success is False
    assert "Invalid arguments" in result.message

def test_validation_valid_arguments():
    with patch('app.agent.tools.create_task') as mock_create_task:
        mock_create_task.return_value = 1
        result = execute_tool("create_task", {"title": "Test Task", "priority": "high"})
        assert result.success is True
        assert result.data["task_id"] == 1

def test_safety_destructive_requires_confirmation():
    # delete_task is DESTRUCTIVE
    session_id = "test_session_1"
    result = execute_tool("delete_task", {"task_id": 1}, session_id=session_id)
    assert result.success is False
    assert "Confirmation required" in result.message

    pending = get_pending_action(session_id)
    assert pending is not None
    assert pending["tool_name"] == "delete_task"
    clear_pending_action(session_id)

def test_safety_cancel_prevents_execution():
    session_id = "test_session_2"
    set_pending_action(session_id, "delete_task", {"task_id": 1}, "Delete?")

    request = AgentRequest(message="No", session_id=session_id)
    response = handle_request(request)
    assert response["success"] is True
    assert response["status"] == "CANCELLED"
    assert get_pending_action(session_id) is None

def test_safety_confirm_executes():
    session_id = "test_session_3"
    set_pending_action(session_id, "delete_task", {"task_id": 1}, "Delete?")

    with patch('app.agent.tools.delete_task') as mock_delete:
        request = AgentRequest(message="Yes", session_id=session_id)
        response = handle_request(request)
        assert response["success"] is True
        assert response["status"] == "SUCCESS"
        mock_delete.assert_called_once_with(task_id=1, session_id=session_id)

def test_executor_handler_failure():
    with patch('app.agent.tools.get_tasks') as mock_get:
        mock_get.side_effect = Exception("DB Error")
        result = execute_tool("list_tasks", {})
        assert result.success is False
        assert "error occurred" in result.message

def test_executor_unknown_tool():
    result = execute_tool("unknown", {})
    assert result.success is False
    assert "Tool not found" in result.message

@patch('app.agent.agent.generate_gemini_response')
def test_agent_multi_step(mock_gemini):
    # Mock Gemini returning a multi-step plan
    mock_gemini.return_value = (
        '''{"classification": "MULTI-STEP ACTION", "plans": [
            {"type": "tool", "tool_name": "create_task", "arguments": {"title": "Learn React", "priority": "high"}},
            {"type": "tool", "tool_name": "create_reminder", "arguments": {"title": "Learn React", "reminder_date": "2026-10-10", "reminder_time": "10:00"}}
        ]}''',
        None
    )

    with patch('app.agent.tools.create_task') as mock_task, \
         patch('app.agent.tools.create_reminder') as mock_rem:
        mock_task.return_value = 1
        mock_rem.return_value = 2

        req = AgentRequest(message="Create a task to learn React and remind me tomorrow at 10 AM.")
        resp = handle_request(req)

        assert resp["success"] is True
        assert mock_task.called
        assert mock_rem.called

@patch('app.agent.agent.generate_gemini_response')
def test_agent_gemini_fallback(mock_gemini):
    # Simulate Gemini failure
    mock_gemini.return_value = (None, "Rate limit exceeded (HTTP 429).")

    req = AgentRequest(message="List my pending tasks")
    # Will fallback to process_message deterministic intent
    with patch('app.agent.agent.fallback_process_message') as mock_fallback:
        mock_fallback.return_value = {"success": True, "message": "Here are tasks", "intent": "list_tasks"}

        resp = handle_request(req)
        assert resp["success"] is True
        assert resp["fallback"] is True
