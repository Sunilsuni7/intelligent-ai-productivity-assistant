from typing import List, Dict, Any
from app.database.database import get_connection
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def _get_ist_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))

def get_completion_trend(days: int = 7) -> List[Dict[str, Any]]:
    """
    Returns completion counts per day for the last N days.
    NOTE: Older tasks might not have 'completed_at' timestamps as this was added in Phase 16.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # We look for completed_at timestamps
    cursor.execute("SELECT completed_at FROM tasks WHERE status = 'completed' AND completed_at IS NOT NULL")
    b_tasks = [r["completed_at"] for r in cursor.fetchall()]

    cursor.execute("SELECT completed_at FROM plan_tasks WHERE status = 'completed' AND completed_at IS NOT NULL")
    p_tasks = [r["completed_at"] for r in cursor.fetchall()]
    conn.close()

    all_timestamps = b_tasks + p_tasks

    now = _get_ist_now().date()
    trend = []

    for i in range(days - 1, -1, -1):
        target_date = now - timedelta(days=i)
        target_str = target_date.strftime("%Y-%m-%d")

        count = sum(1 for ts in all_timestamps if ts and ts[:10] == target_str)
        trend.append({
            "date": target_str,
            "completed": count
        })

    return trend

def get_weekly_comparison() -> Dict[str, Any]:
    trend = get_completion_trend(14)
    # Split into this week (last 7 days) and previous week (first 7 days)
    if len(trend) != 14:
        return {}

    prev_week = sum(t["completed"] for t in trend[:7])
    this_week = sum(t["completed"] for t in trend[7:])

    if prev_week == 0:
        change = float('inf') if this_week > 0 else 0.0
    else:
        change = ((this_week - prev_week) / prev_week) * 100

    return {
        "this_week": this_week,
        "previous_week": prev_week,
        "change_percentage": change
    }
