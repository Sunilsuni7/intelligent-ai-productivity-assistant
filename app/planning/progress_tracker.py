from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from app.planning.planning_models import PlanProgress

def detect_overdue_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    overdue = []
    now = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    for t in tasks:
        if t["status"] == "pending" and t.get("due_date"):
            try:
                due = datetime.strptime(t["due_date"][:10], "%Y-%m-%d").date()
                if (due - now).days < 0:
                    overdue.append(t)
            except:
                pass
    return overdue

def get_progress(tasks: List[Dict[str, Any]]) -> PlanProgress:
    total = len(tasks)
    if total == 0:
        return PlanProgress()

    completed = sum(1 for t in tasks if t["status"] == "completed")
    pending = sum(1 for t in tasks if t["status"] == "pending")
    overdue = len(detect_overdue_tasks(tasks))

    perc = (completed / total) * 100

    return PlanProgress(
        total_tasks=total,
        completed_tasks=completed,
        pending_tasks=pending,
        overdue_tasks=overdue,
        completion_percentage=perc
    )
