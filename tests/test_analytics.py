import pytest
from app.database.database import get_connection, create_tables
from app.analytics.metrics import get_task_metrics, get_priority_breakdown, get_overdue_analysis, get_project_progress
from app.analytics.trends import get_completion_trend, get_weekly_comparison
from app.analytics.report_generator import get_productivity_summary, generate_weekly_report
from app.analytics.insights import get_rule_based_insights
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

@pytest.fixture(autouse=True)
def setup_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS tasks")
    cursor.execute("DROP TABLE IF EXISTS plan_tasks")
    conn.commit()
    conn.close()

    create_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM project_plans")
    cursor.execute("DELETE FROM milestones")
    conn.commit()
    conn.close()

def _add_task(status="pending", priority="medium", due_date=None, completed_at=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, status, priority, due_date, completed_at) VALUES (?, ?, ?, ?, ?)",
        ("Test", status, priority, due_date, completed_at)
    )
    conn.commit()
    conn.close()

def test_task_metrics():
    _add_task(status="completed")
    _add_task(status="pending")

    m = get_task_metrics()
    assert m.total_tasks == 2
    assert m.completed_tasks == 1
    assert m.pending_tasks == 1
    assert m.completion_rate == 50.0

def test_overdue_analysis():
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    past = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    _add_task(status="pending", due_date=past)
    _add_task(status="completed", due_date=past) # Not overdue because it's completed

    m = get_task_metrics()
    assert m.overdue_tasks == 1

    analysis = get_overdue_analysis()
    assert analysis["count"] == 1

def test_priority_breakdown():
    _add_task(status="completed", priority="high")
    _add_task(status="pending", priority="high")
    _add_task(status="completed", priority="low")

    pb = get_priority_breakdown()
    assert pb.high_total == 2
    assert pb.high_completed == 1
    assert pb.low_total == 1

def test_completion_trends():
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    today_str = now.strftime("%Y-%m-%d %H:%M:%S")
    past_str = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    _add_task(status="completed", completed_at=today_str)
    _add_task(status="completed", completed_at=past_str)

    trend = get_completion_trend(7)
    assert len(trend) == 7
    # last item is today
    assert trend[-1]["completed"] == 1
    assert trend[-2]["completed"] == 1

def test_weekly_comparison():
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    # One completed this week
    _add_task(status="completed", completed_at=now.strftime("%Y-%m-%d %H:%M:%S"))
    # Two completed last week
    past = now - timedelta(days=8)
    _add_task(status="completed", completed_at=past.strftime("%Y-%m-%d %H:%M:%S"))
    _add_task(status="completed", completed_at=past.strftime("%Y-%m-%d %H:%M:%S"))

    comp = get_weekly_comparison()
    assert comp["this_week"] == 1
    assert comp["previous_week"] == 2
    assert comp["change_percentage"] == -50.0

def test_rule_based_insights():
    _add_task(status="pending", priority="high", due_date="1999-01-01") # overdue
    _add_task(status="completed")

    insights = get_rule_based_insights()
    types = [i.type for i in insights]
    assert "negative" in types # Overdue

def test_productivity_summary():
    _add_task(status="completed", priority="high")
    _add_task(status="completed", priority="medium")

    summary = get_productivity_summary()
    assert summary.tasks.total_tasks == 2
    assert summary.tasks.completion_rate == 100.0
    assert summary.productivity_score == 100.0 # 50% * 1 + 30% * 1 + 20% * 1

def test_generate_weekly_report():
    rep = generate_weekly_report()
    assert rep["title"] == "Weekly Productivity Report"
    assert "task_summary" in rep
    assert "insights" in rep
