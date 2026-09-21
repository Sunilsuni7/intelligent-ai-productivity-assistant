import os
import pytest
import app.database.database as db_module
db_module.DB_PATH = "test_productivity.db"

from app.tasks.task_manager import create_task, get_tasks, complete_task, delete_task
from app.reminders.reminder_manager import create_reminder, get_reminders, complete_reminder, delete_reminder

@pytest.fixture(autouse=True)
def setup_teardown():
    db_module.create_tables()
    conn = db_module.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks")
    c.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()
    yield

def test_task_lifecycle():
    create_task(title="Learn Python DSA", priority="High", session_id="default")
    tasks = get_tasks(status="pending", session_id="default")
    assert len(tasks) == 1
    task_id = tasks[0]["id"]
    complete_task(task_id=task_id, session_id="default")
    assert len(get_tasks(status="pending", session_id="default")) == 0
    delete_task(task_id=task_id, session_id="default")
    assert len(get_tasks(status="pending", session_id="default")) == 0

def test_reminder_lifecycle():
    create_reminder(title="Submit Resume", reminder_date="2026-09-19", reminder_time="10:00", session_id="default")
    rems = get_reminders(status="pending", session_id="default")
    assert len(rems) == 1
    r_id = rems[0]["id"]
    complete_reminder(reminder_id=r_id, session_id="default")
    assert len(get_reminders(status="pending", session_id="default")) == 0
    delete_reminder(reminder_id=r_id, session_id="default")
    assert len(get_reminders(status="pending", session_id="default")) == 0

