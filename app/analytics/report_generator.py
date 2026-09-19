from typing import Dict, Any
from app.analytics.analytics_models import ProductivitySummary
from app.analytics.metrics import get_task_metrics, get_priority_breakdown, get_project_progress, get_reminder_metrics
from app.analytics.trends import get_weekly_comparison
from app.analytics.insights import get_rule_based_insights

def get_productivity_summary() -> ProductivitySummary:
    summary = ProductivitySummary()
    summary.tasks = get_task_metrics()
    summary.priorities = get_priority_breakdown()

    projects = get_project_progress()
    summary.active_projects_count = len(projects)
    summary.completed_milestones_count = sum(p.milestones_completed for p in projects)
    summary.pending_milestones_count = sum(p.milestones_remaining for p in projects)

    summary.reminders = get_reminder_metrics()

    # Calculate a transparent Productivity Score (out of 100)
    # Weight: 50% Completion Rate, 30% Non-Overdue Rate, 20% Priority Completion
    c_rate = summary.tasks.completion_rate
    no_rate = 100.0 - summary.tasks.overdue_rate

    p_comp = 0
    if summary.priorities.high_total > 0:
        p_comp = (summary.priorities.high_completed / summary.priorities.high_total) * 100

    score = (c_rate * 0.5) + (no_rate * 0.3) + (p_comp * 0.2)
    summary.productivity_score = min(max(score, 0), 100)

    summary.insights = get_rule_based_insights()

    return summary

def generate_weekly_report() -> Dict[str, Any]:
    summary = get_productivity_summary()
    comp = get_weekly_comparison()

    report = {
        "title": "Weekly Productivity Report",
        "task_summary": summary.tasks.model_dump(),
        "priority_summary": summary.priorities.model_dump(),
        "productivity_score": round(summary.productivity_score, 1),
        "weekly_comparison": comp,
        "insights": [i.model_dump() for i in summary.insights]
    }
    return report
