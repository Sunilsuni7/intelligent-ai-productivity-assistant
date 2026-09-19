import os
import pytest
from fastapi.testclient import TestClient

# Mock DB path before importing the app
import app.database.database as db_module
db_module.DB_PATH = "test_productivity.db"

from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    db_module.create_tables()
    yield
    if os.path.exists("test_productivity.db"):
        os.remove("test_productivity.db")

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_chat_task_creation():
    response = client.post("/chat", json={"message": "create a task to test tasks"})
    assert response.status_code == 200
