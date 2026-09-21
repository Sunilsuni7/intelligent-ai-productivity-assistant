import pytest
from app.memory.memory_manager import add_memory, list_memories, deactivate_memory, contains_sensitive_info
from app.memory.memory_retriever import retrieve_relevant_memories
from app.database.database import get_connection

@pytest.fixture(autouse=True)
def setup_db():
    from app.database.database import create_tables
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories")
    conn.commit()
    conn.close()

def test_add_memory():
    res = add_memory(session_id="default", content="I love Python")
    assert res["success"] is True
    mems = list_memories()
    assert len(mems) == 1
    assert mems[0]["content"] == "I love Python"

def test_deduplication():
    add_memory(session_id="default", content="My project is AI Productivity Assistant")
    mems1 = list_memories()
    assert len(mems1) == 1

    # Adding a similar memory should update/supersede it, keeping length 1
    add_memory(session_id="default", content="My main project is AI Productivity Assistant")
    mems2 = list_memories()
    assert len(mems2) == 1

    add_memory(session_id="default", content="I like apples")
    assert len(list_memories()) == 2

def test_sensitive_info():
    assert contains_sensitive_info("My password = password123") is True
    assert contains_sensitive_info("My API_KEY=abcxyz123") is True
    assert contains_sensitive_info("I live on Earth") is False

    res = add_memory(session_id="default", content="My password = password123")
    assert res["success"] is False
    assert len(list_memories()) == 0

def test_deactivate_memory():
    add_memory(session_id="default", content="I like bananas")
    res = deactivate_memory(session_id="default", content_query="bananas")
    assert res["success"] is True
    assert len(list_memories()) == 0

def test_retrieve_relevant_memories():
    add_memory(session_id="default", content="User works at Google", importance="high")
    add_memory(session_id="default", content="User likes to play tennis", importance="low")

    mems = retrieve_relevant_memories("Where do I work?")
    assert len(mems) >= 1
    assert "Google" in mems[0]["content"]

    # Checking importance boost
    # Since "work" intersects nicely, it'll rank highly.
