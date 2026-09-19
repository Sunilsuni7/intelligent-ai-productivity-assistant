from typing import List, Dict, Any, Optional
from app.database.database import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo
from app.planning.planning_models import Goal, ProjectPlan, Milestone, PlanTask, TaskDependency

def _get_ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

def create_goal(title: str, description: str = None, target_date: str = None, priority: str = "medium") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = _get_ist_now()
    cursor.execute("""
        INSERT INTO goals (title, description, target_date, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?)
    """, (title, description, target_date, priority, now, now))
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return goal_id

def list_goals() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE status != 'deleted' ORDER BY id DESC")
    goals = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return goals

def create_project_plan(goal_id: Optional[int], title: str, description: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = _get_ist_now()
    cursor.execute("""
        INSERT INTO project_plans (goal_id, title, description, status, created_at, updated_at)
        VALUES (?, ?, ?, 'active', ?, ?)
    """, (goal_id, title, description, now, now))
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return plan_id

def create_milestone(plan_id: int, title: str, description: str = None, order_index: int = 0, target_date: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO milestones (plan_id, title, description, order_index, target_date, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (plan_id, title, description, order_index, target_date))
    milestone_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return milestone_id

def create_plan_task(milestone_id: int, title: str, description: str = None, priority: str = "medium",
                     estimated_minutes: int = 60, due_date: str = None, order_index: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plan_tasks (milestone_id, title, description, priority, estimated_minutes, due_date, status, order_index)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (milestone_id, title, description, priority, estimated_minutes, due_date, order_index))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def add_task_dependency(task_id: int, depends_on_task_id: int, dependency_type: str = "blocks"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO task_dependencies (task_id, depends_on_task_id, dependency_type)
        VALUES (?, ?, ?)
    """, (task_id, depends_on_task_id, dependency_type))
    conn.commit()
    conn.close()

def get_project_plan(plan_id: int) -> Optional[ProjectPlan]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM project_plans WHERE id = ?", (plan_id,))
    p_row = cursor.fetchone()
    if not p_row:
        conn.close()
        return None

    plan = ProjectPlan(**dict(p_row))

    cursor.execute("SELECT * FROM milestones WHERE plan_id = ? ORDER BY order_index", (plan_id,))
    m_rows = cursor.fetchall()

    for m_row in m_rows:
        milestone = Milestone(**dict(m_row))
        cursor.execute("SELECT * FROM plan_tasks WHERE milestone_id = ? ORDER BY order_index", (milestone.id,))
        t_rows = cursor.fetchall()
        for t_row in t_rows:
            task = PlanTask(**dict(t_row))
            # Get dependencies
            cursor.execute("SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?", (task.id,))
            task.dependencies = [row['depends_on_task_id'] for row in cursor.fetchall()]
            milestone.tasks.append(task)
        plan.milestones.append(milestone)

    conn.close()
    return plan

def get_active_tasks() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plan_tasks WHERE status = 'pending'")
    tasks = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE plan_tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()
