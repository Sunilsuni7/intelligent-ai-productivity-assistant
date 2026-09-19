from typing import List, Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

def calculate_priority_score(task: Dict[str, Any], dependencies: List[Dict[str, int]], all_tasks: List[Dict[str, Any]]) -> float:
    score = 0.0

    # Base priority
    priority = task.get("priority", "medium").lower()
    if priority == "high":
        score += 50
    elif priority == "medium":
        score += 30
    else:
        score += 10

    # Check if due soon / overdue
    due_date = task.get("due_date")
    if due_date:
        try:
            due = datetime.strptime(due_date[:10], "%Y-%m-%d").date()
            now = datetime.now(ZoneInfo("Asia/Kolkata")).date()
            diff = (due - now).days
            if diff < 0:
                score += 100 # Overdue
            elif diff <= 1:
                score += 80 # Due today/tomorrow
            elif diff <= 7:
                score += 40
        except:
            pass

    # Blocking downstream tasks
    # How many tasks depend on THIS task?
    tid = task["id"]
    blocking_count = sum(1 for d in dependencies if d["depends_on_task_id"] == tid)
    score += (blocking_count * 20)

    # Is it blocked?
    blocked_by = [d["depends_on_task_id"] for d in dependencies if d["task_id"] == tid]
    active_blockers = 0
    for b in blocked_by:
        for t in all_tasks:
            if t["id"] == b and t["status"] == "pending":
                active_blockers += 1

    if active_blockers > 0:
        score -= 1000 # Severely demote tasks that cannot be started

    return score

def suggest_next_best_action(tasks: List[Dict[str, Any]], dependencies: List[Dict[str, int]]) -> Optional[Dict[str, Any]]:
    pending_tasks = [t for t in tasks if t["status"] == "pending"]
    if not pending_tasks:
        return None

    scored = []
    for t in pending_tasks:
        score = calculate_priority_score(t, dependencies, tasks)
        scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0]

    if best[0] < -500:
        return None # Everything is blocked!

    return best[1]
