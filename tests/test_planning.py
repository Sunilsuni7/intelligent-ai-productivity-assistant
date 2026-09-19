import pytest
from app.database.database import get_connection, create_tables
from app.planning.planning_manager import create_goal, create_project_plan, create_milestone, create_plan_task, add_task_dependency, get_active_tasks, get_project_plan
from app.planning.dependency_manager import check_circular_dependency
from app.planning.prioritizer import calculate_priority_score, suggest_next_best_action
from app.planning.progress_tracker import get_progress, detect_overdue_tasks
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

@pytest.fixture(autouse=True)
def setup_db():
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM task_dependencies")
    cursor.execute("DELETE FROM plan_tasks")
    cursor.execute("DELETE FROM milestones")
    cursor.execute("DELETE FROM project_plans")
    cursor.execute("DELETE FROM goals")
    conn.commit()
    conn.close()

def test_goal_and_plan_creation():
    gid = create_goal("Learn React")
    assert gid > 0
    pid = create_project_plan(gid, "React Plan")
    assert pid > 0
    mid = create_milestone(pid, "Hooks")
    assert mid > 0
    tid = create_plan_task(mid, "Learn useState")
    assert tid > 0

    plan = get_project_plan(pid)
    assert plan is not None
    assert plan.title == "React Plan"
    assert len(plan.milestones) == 1
    assert len(plan.milestones[0].tasks) == 1
    assert plan.milestones[0].tasks[0].title == "Learn useState"

def test_circular_dependency():
    deps = [{"task_id": 1, "depends_on_task_id": 2}]
    # We want to add 2 depends on 1
    is_circular = check_circular_dependency(2, 1, deps)
    assert is_circular is True

    # 1 -> 2 -> 3
    deps2 = [{"task_id": 1, "depends_on_task_id": 2}, {"task_id": 2, "depends_on_task_id": 3}]
    # if 3 depends on 1? Yes, circular
    assert check_circular_dependency(3, 1, deps2) is True

    # 3 depends on 4? Not circular
    assert check_circular_dependency(3, 4, deps2) is False

def test_prioritizer():
    tasks = [
        {"id": 1, "title": "A", "priority": "high", "status": "pending"},
        {"id": 2, "title": "B", "priority": "medium", "status": "pending"}
    ]
    deps = [{"task_id": 2, "depends_on_task_id": 1}] # B depends on A

    nba = suggest_next_best_action(tasks, deps)
    assert nba["id"] == 1 # A blocks B and is High priority

def test_overdue_tasks():
    now = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    past = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    future = (now + timedelta(days=2)).strftime("%Y-%m-%d")

    tasks = [
        {"id": 1, "status": "pending", "due_date": past},
        {"id": 2, "status": "pending", "due_date": future}
    ]

    overdue = detect_overdue_tasks(tasks)
    assert len(overdue) == 1
    assert overdue[0]["id"] == 1

def test_progress():
    tasks = [
        {"status": "completed"},
        {"status": "pending", "due_date": "2000-01-01"}
    ]
    prog = get_progress(tasks)
    assert prog.total_tasks == 2
    assert prog.completed_tasks == 1
    assert prog.overdue_tasks == 1
    assert prog.completion_percentage == 50.0
