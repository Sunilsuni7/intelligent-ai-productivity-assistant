import pytest
from unittest.mock import patch, MagicMock
from app.agent.agent import handle_request
from app.api.routes import ChatRequest

@pytest.fixture
def mock_execute():
    with patch("app.agent.agent.execute_tool") as mock_exec:
        # We need execute_tool to return a successful ToolResult
        from app.agent.models import ToolResult
        mock_exec.return_value = ToolResult(tool_name="mocked_tool", success=True, message="Mocked success", data={})
        yield mock_exec

def run_nlu_test(message, mock_exec):
    req = ChatRequest(message=message, session_id="nlu-test")
    resp = handle_request(req)
    # Get all the tools that were called
    tools_called = [call.args[0] for call in mock_exec.call_args_list]
    args_called = [call.args[1] for call in mock_exec.call_args_list]
    mock_exec.reset_mock()
    return tools_called, args_called

def test_nlu_open_youtube(mock_execute):
    variations = [
        "Open YouTube.",
        "Can you open YouTube?",
        "Take me to YouTube.",
        "Launch YouTube.",
        "Go to YouTube."
    ]
    for var in variations:
        tools, args = run_nlu_test(var, mock_execute)
        # It might use 'open_website', 'search_google', 'search_media', or 'open_application' depending on Gemini.
        # Generally, it should call at least one tool.
        assert len(tools) > 0, f"Failed on: {var}"

def test_nlu_close_chrome(mock_execute):
    variations = [
        "Close Chrome.",
        "Can you close Chrome?",
        "Exit Chrome.",
        "Close the browser."
    ]
    for var in variations:
        tools, args = run_nlu_test(var, mock_execute)
        assert len(tools) > 0, f"Failed on: {var}"
        # Typically close_browser or close_application
        assert tools[0] in ["close_browser", "close_application"]

def test_nlu_media(mock_execute):
    tools, args = run_nlu_test("Put on some Python videos.", mock_execute)
    assert len(tools) > 0
    assert tools[0] in ["play_media", "search_youtube"]

    tools, args = run_nlu_test("Play Arijit Singh songs on YouTube.", mock_execute)
    assert len(tools) > 0
    assert tools[0] in ["play_media", "search_youtube"]

    tools, args = run_nlu_test("Pause it.", mock_execute)
    assert len(tools) > 0
    assert tools[0] == "pause_media"

def test_nlu_multi_step(mock_execute):
    tools, args = run_nlu_test("Open YouTube and play Python DSA videos.", mock_execute)
    # Might do open_website and play_media, or just play_media with query
    assert len(tools) >= 1
    
    tools, args = run_nlu_test("Open Chrome and search for React tutorials.", mock_execute)
    # Typically open_application -> search_google
    assert len(tools) >= 1

