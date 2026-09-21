import pytest
from app.ai.assistant import save_chat_history, get_chat_history
from app.database.database import create_tables, get_connection

@pytest.fixture(autouse=True)
def setup_teardown():
    create_tables()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()
    yield

def test_session_isolation():
    # Session A writes private data
    save_chat_history(session_id="session_A", user_message="My secret is 123", assistant_response="Got it.")
    
    # Session B writes other data
    save_chat_history(session_id="session_B", user_message="What is my secret?", assistant_response="I don't know.")
    
    # Session A reads
    hist_A = get_chat_history("session_A", limit=5)
    assert len(hist_A) == 1
    assert "123" in hist_A[0]["user_message"]
    
    # Session B reads
    hist_B = get_chat_history("session_B", limit=5)
    assert len(hist_B) == 1
    assert "123" not in hist_B[0]["user_message"]
    assert "I don't know" in hist_B[0]["assistant_response"]
    
    # This verifies strict isolation on the backend.
