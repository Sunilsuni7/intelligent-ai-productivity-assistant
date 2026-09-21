import pytest
from unittest.mock import patch, MagicMock
from app.agent.agent import handle_request
from app.agent.models import AgentRequest
from app.agent.executor import execute_tool
from app.agent.tool_registry import ToolDefinition
from app.agent.safety import RiskLevel

@pytest.fixture
def mock_gemini_response():
    with patch('app.agent.agent.generate_gemini_response') as mock_gemini:
        yield mock_gemini

def create_plan_json(classification, plans):
    import json
    return json.dumps({
        "classification": classification,
        "plans": plans,
        "response": "Hello" if classification == "CONVERSATION" else None
    })

def test_single_step_execution(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("TOOL ACTION", [
        {"type": "tool", "tool_name": "get_cpu_usage", "arguments": {}}
    ]), None)
    
    with patch('app.agent.system_info_tools.psutil') as mock_psutil:
        mock_psutil.cpu_percent.return_value = 10.0
        req = AgentRequest(message="What is my CPU?")
        res = handle_request(req)
        
        assert res["success"] is True
        assert "10.0%" in res["message"]
        exec_res = res["execution_result"]
        assert exec_res["completed_steps"] == 1
        assert len(exec_res["step_results"]) == 1
        assert exec_res["step_results"][0]["success"] is True

def test_two_step_successful_execution(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("MULTI-STEP ACTION", [
        {"type": "tool", "tool_name": "create_folder", "arguments": {"folder_name": "test_folder_123", "base_dir": "desktop"}},
        {"type": "tool", "tool_name": "get_cpu_usage", "arguments": {}}
    ]), None)
    
    with patch('app.agent.file_tools.resolve_safe_path') as mock_resolve, \
         patch('app.agent.system_info_tools.psutil') as mock_psutil:
         
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_resolve.return_value = mock_path
        
        mock_psutil.cpu_percent.return_value = 20.0
        
        req = AgentRequest(message="Create folder and get cpu")
        res = handle_request(req)
        
        assert res["success"] is True
        exec_res = res["execution_result"]
        assert exec_res["completed_steps"] == 2
        assert len(exec_res["step_results"]) == 2
        assert exec_res["step_results"][0]["tool_name"] == "create_folder"
        assert exec_res["step_results"][1]["tool_name"] == "get_cpu_usage"
        
        assert "Created the test_folder_123 folder" in res["message"]
        assert "20.0%" in res["message"]

def test_three_step_successful_execution(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("MULTI-STEP ACTION", [
        {"type": "tool", "tool_name": "get_cpu_usage", "arguments": {}},
        {"type": "tool", "tool_name": "get_memory_usage", "arguments": {}},
        {"type": "tool", "tool_name": "get_disk_usage", "arguments": {}}
    ]), None)
    
    with patch('app.agent.system_info_tools.psutil') as mock_psutil:
        req = AgentRequest(message="Get all system info")
        res = handle_request(req)
        
        assert res["success"] is True
        exec_res = res["execution_result"]
        assert exec_res["completed_steps"] == 3
        assert len(exec_res["step_results"]) == 3

def test_failed_first_step_stops_execution(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("MULTI-STEP ACTION", [
        {"type": "tool", "tool_name": "create_folder", "arguments": {"folder_name": "projects", "base_dir": "desktop"}},
        {"type": "tool", "tool_name": "get_cpu_usage", "arguments": {}}
    ]), None)
    
    with patch('app.agent.executor.get_tool') as mock_get_tool:
        # Provide a mock tool that fails by raising exception
        def failing_handler(**kwargs):
            raise Exception("Permission denied")
            
        mock_get_tool.return_value = ToolDefinition(
            name="create_folder",
            description="",
            input_schema={"type": "object", "properties": {"folder_name": {"type": "string"}, "base_dir": {"type": "string"}}},
            handler=failing_handler,
            risk_level=RiskLevel.READ,
            requires_confirmation=False
        )
        
        req = AgentRequest(message="Create folder and get cpu")
        res = handle_request(req)
        
        assert res["success"] is False
        exec_res = res["execution_result"]
        assert exec_res["completed_steps"] == 0
        assert exec_res["failed_step"] == 1
        assert len(exec_res["step_results"]) == 1
        assert "Stopped execution" in res["message"]

def test_failed_second_step(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("MULTI-STEP ACTION", [
        {"type": "tool", "tool_name": "get_cpu_usage", "arguments": {}},
        {"type": "tool", "tool_name": "create_folder", "arguments": {"folder_name": "projects", "base_dir": "desktop"}}
    ]), None)
    
    # We will let step 1 pass (get_cpu_usage) but mock step 2 to fail
    original_get_tool = execute_tool # We'll just patch get_tool
    
    with patch('app.agent.executor.get_tool') as mock_get_tool:
        from app.agent.tool_registry import get_tool as real_get_tool
        
        def side_effect(tool_name):
            if tool_name == "create_folder":
                def failing_handler(**kwargs):
                    raise Exception("Disk full")
                return ToolDefinition(
                    name="create_folder",
                    description="",
                    input_schema={"type": "object", "properties": {"folder_name": {"type": "string"}, "base_dir": {"type": "string"}}},
                    handler=failing_handler,
                    risk_level=RiskLevel.READ,
                    requires_confirmation=False
                )
            return real_get_tool(tool_name)
            
        mock_get_tool.side_effect = side_effect
        
        req = AgentRequest(message="Get cpu and create folder")
        res = handle_request(req)
        
        assert res["success"] is False
        exec_res = res["execution_result"]
        assert exec_res["completed_steps"] == 1
        assert exec_res["failed_step"] == 2
        assert len(exec_res["step_results"]) == 2
        assert exec_res["step_results"][0]["success"] is True
        assert exec_res["step_results"][1]["success"] is False

def test_unknown_tool_rejection(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("TOOL ACTION", [
        {"type": "tool", "tool_name": "hack_mainframe", "arguments": {}}
    ]), None)
    
    req = AgentRequest(message="Hack the mainframe")
    res = handle_request(req)
    
    assert res["success"] is False
    exec_res = res["execution_result"]
    assert exec_res["completed_steps"] == 0
    assert exec_res["step_results"][0]["success"] is False
    assert "not registered" in exec_res["step_results"][0]["message"]

def test_invalid_argument_rejection(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("TOOL ACTION", [
        {"type": "tool", "tool_name": "create_folder", "arguments": {"wrong_arg": "value"}}
    ]), None)
    
    req = AgentRequest(message="Create a folder badly")
    res = handle_request(req)
    
    assert res["success"] is False
    exec_res = res["execution_result"]
    assert exec_res["step_results"][0]["success"] is False
    assert "required" in exec_res["step_results"][0]["message"]

def test_normal_conversation(mock_gemini_response):
    mock_gemini_response.return_value = (create_plan_json("CONVERSATION", []), None)
    
    req = AgentRequest(message="What is Python?")
    res = handle_request(req)
    
    assert res["success"] is True
    assert res["message"] == "Hello"
    assert "execution_result" not in res # Doesn't run tools
