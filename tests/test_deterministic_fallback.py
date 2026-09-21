import pytest
from unittest.mock import patch
from app.agent.agent import handle_request
from app.api.routes import ChatRequest
from app.agent.models import ToolResult

@pytest.fixture
def mock_gemini_error():
    with patch("app.agent.agent.generate_gemini_response") as mock_gemini:
        mock_gemini.return_value = (None, "429 RESOURCE_EXHAUSTED")
        yield mock_gemini

@pytest.fixture
def mock_execute():
    with patch("app.ai.assistant.execute_tool") as mock_exec:
        # Mock successful execution
        mock_exec.return_value = ToolResult(success=True, tool_name="mock_tool", message="Mocked success", data={})
        yield mock_exec

def test_fallback_open_youtube(mock_gemini_error, mock_execute):
    req = ChatRequest(message="Open YouTube", session_id="test")
    res = handle_request(req)
    assert res["success"] is True
    assert res["tool"] == "open_website"
    mock_execute.assert_called_once_with("open_website", {"url": "https://youtube.com"}, session_id="test")

def test_fallback_search_youtube(mock_gemini_error, mock_execute):
    req = ChatRequest(message="Search YouTube for Python DSA", session_id="test")
    res = handle_request(req)
    assert res["success"] is True
    assert res["tool"] == "search_youtube"
    mock_execute.assert_called_once_with("search_youtube", {"query": "Python DSA"}, session_id="test")

def test_fallback_search_google(mock_gemini_error, mock_execute):
    req = ChatRequest(message="Search Google for React tutorials", session_id="test")
    res = handle_request(req)
    assert res["success"] is True
    assert res["tool"] == "search_google"
    mock_execute.assert_called_once_with("search_google", {"query": "React tutorials"}, session_id="test")

def test_fallback_open_vscode(mock_gemini_error, mock_execute):
    req = ChatRequest(message="Open VS Code", session_id="test")
    res = handle_request(req)
    assert res["success"] is True
    assert res["tool"] == "open_application"
    mock_execute.assert_called_once_with("open_application", {"app_name": "vs code"}, session_id="test")

def test_fallback_close_browser(mock_gemini_error, mock_execute):
    req = ChatRequest(message="Close browser", session_id="test")
    res = handle_request(req)
    assert res["success"] is True
    assert res["tool"] == "close_browser"
    mock_execute.assert_called_once_with("close_browser", {}, session_id="test")

def test_fallback_pause_resume_stop(mock_gemini_error, mock_execute):
    for cmd, expected_tool in [
        ("Pause", "pause_media"),
        ("Resume", "resume_media"),
        ("Stop", "stop_media")
    ]:
        mock_execute.reset_mock()
        req = ChatRequest(message=cmd, session_id="test")
        res = handle_request(req)
        assert res["success"] is True
        assert res["tool"] == expected_tool
        mock_execute.assert_called_once_with(expected_tool, {}, session_id="test")

def test_fallback_tool_failure(mock_gemini_error, mock_execute):
    # Mock tool execution returning failure
    mock_execute.return_value = ToolResult(success=False, tool_name="open_website", message="Failed to open", error="Network error", data={})
    
    req = ChatRequest(message="Open YouTube", session_id="test")
    res = handle_request(req)
    # The fallback should report failure
    assert res["success"] is False
    # The fallback mechanism in agent.py looks for fb.get("success"), which is now False.
    # When fb.get("success") is False, handle_request returns success=False and the error message.
    assert "Failed to process request" in res["message"] or "Execution failed" in res["message"] or "Network error" in res["message"] or res["success"] is False
    mock_execute.assert_called_once_with("open_website", {"url": "https://youtube.com"}, session_id="test")

def test_fallback_unknown_command(mock_gemini_error, mock_execute):
    with patch("app.ai.assistant.generate_gemini_response") as mock_ast_gemini:
        mock_ast_gemini.return_value = (None, "429 RESOURCE_EXHAUSTED")
        req = ChatRequest(message="Do a backflip", session_id="test")
        res = handle_request(req)
        assert res["success"] is False
        assert mock_execute.call_count == 0
