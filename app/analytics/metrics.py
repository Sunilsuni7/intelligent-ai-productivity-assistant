from typing import List, Dict, Any
from app.database.database import get_connection
from app.analytics.analytics_models import TaskMetrics, PriorityBreakdown, GoalProgress, ProjectProgress, ReminderMetrics
from datetime import datetime
from zoneinfo import ZoneInfo

def _get_ist_now_date() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

def get_task_metrics() -> TaskMetrics:
    conn = get_connection()
    cursor = conn.cursor()

    # Combine tasks and plan_tasks
    cursor.execute("SELECT status, due_date FROM tasks")
    basic_tasks = cursor.fetchall()

    cursor.execute("SELECT status, due_date FROM plan_tasks")
    p_tasks = cursor.fetchall()
    conn.close()

    all_tasks = basic_tasks + p_tasks

    total = len(all_tasks)
    if total == 0:
        return TaskMetrics()

    completed = sum(1 for t in all_tasks if t["status"] == "completed")
    pending = total - completed

    now_date = _get_ist_now_date()
    overdue = 0
    for t in all_tasks:
        if t["status"] == "pending" and t["due_date"]:
            if t["due_date"][:10] < now_date:
                overdue += 1

    comp_rate = (completed / total) * 100 if total > 0 else 0.0
    over_rate = (overdue / total) * 100 if total > 0 else 0.0

    return TaskMetrics(
        total_tasks=total,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue,
        completion_rate=comp_rate,
        overdue_rate=over_rate
    )

def get_priority_breakdown() -> PriorityBreakdown:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT priority, status FROM tasks")
    b_tasks = cursor.fetchall()

    cursor.execute("SELECT priority, status FROM plan_tasks")
    p_tasks = cursor.fetchall()
    conn.close()

    all_tasks = b_tasks + p_tasks

    pb = PriorityBreakdown()
    for t in all_tasks:
        p = (t["priority"] or "medium").lower()
        is_comp = (t["status"] == "completed")

        if p == "high":
            pb.high_total += 1
            if is_comp: pb.high_completed += 1
        elif p == "medium":
            pb.medium_total += 1
            if is_comp: pb.medium_completed += 1
        else:
            pb.low_total += 1
            if is_comp: pb.low_completed += 1

    return pb

def get_project_progress() -> List[ProjectProgress]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM project_plans WHERE status = 'active'")
    plans = cursor.fetchall()

    results = []
    now_date = _get_ist_now_date()

    for p in plans:
        pp = ProjectProgress(plan_id=p["id"], title=p["title"])
        cursor.execute("SELECT id, status FROM milestones WHERE plan_id = ?", (p["id"],))
        milestones = cursor.fetchall()

        pp.milestones_completed = sum(1 for m in milestones if m["status"] == "completed")
        pp.milestones_remaining = len(milestones) - pp.milestones_completed

        for m in milestones:
            cursor.execute("SELECT status, due_date FROM plan_tasks WHERE milestone_id = ?", (m["id"],))
            tasks = cursor.fetchall()
            for t in tasks:
                if t["status"] == "completed":
                    pp.completed_tasks += 1
                else:
                    pp.pending_tasks += 1
                    if t["due_date"] and t["due_date"][:10] < now_date:
                        pp.overdue_tasks += 1

        total_tasks = pp.completed_tasks + pp.pending_tasks
        if total_tasks > 0:
            pp.overall_completion = (pp.completed_tasks / total_tasks) * 100

        results.append(pp)

    conn.close()
    return results

def get_reminder_metrics() -> ReminderMetrics:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, reminder_date FROM reminders")
    reminders = cursor.fetchall()
    conn.close()

    rm = ReminderMetrics()
    now_date = _get_ist_now_date()

    rm.total = len(reminders)
    for r in reminders:
        if r["status"] == "completed":
            rm.completed += 1
        else:
            rm.pending += 1
            if r["reminder_date"] and r["reminder_date"] < now_date:
                rm.overdue += 1

    return rm

def get_overdue_analysis() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now_date = _get_ist_now_date()

    cursor.execute("SELECT id, title, priority, due_date FROM tasks WHERE status = 'pending' AND due_date < ?", (now_date,))
    overdue_b = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, title, priority, due_date FROM plan_tasks WHERE status = 'pending' AND due_date < ?", (now_date,))
    overdue_p = [dict(r) for r in cursor.fetchall()]
    conn.close()

    all_overdue = overdue_b + overdue_p
    all_overdue.sort(key=lambda x: x["due_date"])

    oldest = all_overdue[0] if all_overdue else None

    return {
        "count": len(all_overdue),
        "oldest": oldest,
        "items": all_overdue
    }
