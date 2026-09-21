import pytest
import sqlite3
from app.database.database import get_connection
from app.ai.assistant import save_chat_history, get_chat_history
from app.agent.agent import log_tool_activity

@pytest.fixture(autouse=True)
def setup_test_db():
    from app.database.database import create_tables
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    cursor.execute("DELETE FROM tool_activity")
    conn.commit()
    conn.close()

def test_session_isolation_db():
    # Insert data for Session A
    save_chat_history("session_A", "My favorite color is blue.", "Noted, blue.")
    save_chat_history("session_A", "What is my color?", "Blue.")
    
    # Insert data for Session B
    save_chat_history("session_B", "My favorite color is red.", "Noted, red.")
    
    # Assert isolation
    history_A = get_chat_history("session_A")
    history_B = get_chat_history("session_B")
    
    assert len(history_A) == 2
    assert len(history_B) == 1
    
    assert "blue" in history_A[0]["user_message"].lower() or "blue" in history_A[1]["user_message"].lower()
    assert "red" in history_B[0]["user_message"].lower()
    
    # Ensure B doesn't see A's stuff
    for row in history_B:
        assert "blue" not in row["user_message"].lower()

def test_tool_activity_isolation():
    log_tool_activity("session_A", "text", "open_application", {"app_name": "chrome"}, "SUCCESS", 100)
    log_tool_activity("session_B", "voice", "search_google", {"query": "test"}, "SUCCESS", 200)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT tool_name FROM tool_activity WHERE session_id='session_A'")
    tools_a = [r[0] for r in cursor.fetchall()]
    assert "open_application" in tools_a
    assert "search_google" not in tools_a
    
    cursor.execute("SELECT tool_name FROM tool_activity WHERE session_id='session_B'")
    tools_b = [r[0] for r in cursor.fetchall()]
    assert "search_google" in tools_b
    assert "open_application" not in tools_b
    conn.close()

