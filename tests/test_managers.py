import os
import pytest
import app.database.database as db_module
db_module.DB_PATH = "test_productivity.db"

from app.tasks.task_manager import create_task, get_tasks, complete_task, delete_task
from app.reminders.reminder_manager import create_reminder, get_reminders, complete_reminder, delete_reminder

@pytest.fixture(autouse=True)
def setup_teardown():
    if os.path.exists("test_productivity.db"):
        os.remove("test_productivity.db")

    db_module.create_tables()

    yield

    if os.path.exists("test_productivity.db"):
        os.remove("test_productivity.db")

def test_task_lifecycle():
    create_task("Learn Python DSA", priority="High")
    tasks = get_tasks("pending")
    assert len(tasks) == 1
    task_id = tasks[0]["id"]
    complete_task(task_id)
    assert len(get_tasks("pending")) == 0
    delete_task(task_id)
    assert len(get_tasks()) == 0

def test_reminder_lifecycle():
    create_reminder("Submit Resume", "2026-09-19", "10:00")
    rems = get_reminders("pending")
    assert len(rems) == 1
    r_id = rems[0]["id"]
    complete_reminder(r_id)
    assert len(get_reminders("pending")) == 0
    delete_reminder(r_id)
    assert len(get_reminders()) == 0
