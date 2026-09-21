from app.agent.tool_registry import register_tool
from app.agent.safety import RiskLevel
from app.tasks.task_manager import create_task, get_tasks, complete_task, delete_task
from app.reminders.reminder_manager import create_reminder, get_reminders, complete_reminder, delete_reminder

@register_tool(
    name="create_task",
    description="Create a new task with title, priority, and optional due date.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "due_date": {"type": "string", "description": "Optional due date in YYYY-MM-DD format"}
        },
        "required": ["title", "priority"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_task(title: str, priority: str, due_date: str = None, session_id: str = "default"):
    task_id = create_task(session_id=session_id, title=title, priority=priority, due_date=due_date)
    return {"task_id": task_id, "title": title, "priority": priority, "due_date": due_date}

@register_tool(
    name="list_tasks",
    description="List pending tasks.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_list_tasks(session_id: str = "default"):
    tasks = get_tasks(session_id=session_id, status="pending")
    return {"tasks": [dict(t) for t in tasks]}

@register_tool(
    name="complete_task",
    description="Mark a task as completed.",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_complete_task(task_id: int, session_id: str = "default"):
    complete_task(session_id=session_id, task_id=task_id)
    return {"task_id": task_id, "status": "completed"}

@register_tool(
    name="delete_task",
    description="Permanently delete a task.",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    risk_level=RiskLevel.DESTRUCTIVE,
    requires_confirmation=False
)
def handle_delete_task(task_id: int, session_id: str = "default"):
    delete_task(session_id=session_id, task_id=task_id)
    return {"task_id": task_id, "status": "deleted"}

@register_tool(
    name="create_reminder",
    description="Create a new reminder with title, date, and time.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "reminder_date": {"type": "string", "description": "YYYY-MM-DD format"},
            "reminder_time": {"type": "string", "description": "HH:MM format"}
        },
        "required": ["title", "reminder_date", "reminder_time"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_reminder(title: str, reminder_date: str, reminder_time: str, session_id: str = "default"):
    reminder_id = create_reminder(session_id=session_id, title=title, reminder_date=reminder_date, reminder_time=reminder_time)
    return {"reminder_id": reminder_id, "title": title, "reminder_date": reminder_date, "reminder_time": reminder_time}

@register_tool(
    name="list_reminders",
    description="List pending reminders.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_list_reminders(session_id: str = "default"):
    reminders = get_reminders(session_id=session_id, status="pending")
    return {"reminders": [dict(r) for r in reminders]}

@register_tool(
    name="complete_reminder",
    description="Mark a reminder as completed.",
    input_schema={
        "type": "object",
        "properties": {
            "reminder_id": {"type": "integer"}
        },
        "required": ["reminder_id"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_complete_reminder(reminder_id: int, session_id: str = "default"):
    complete_reminder(session_id=session_id, reminder_id=reminder_id)
    return {"reminder_id": reminder_id, "status": "completed"}

@register_tool(
    name="delete_reminder",
    description="Permanently delete a reminder.",
    input_schema={
        "type": "object",
        "properties": {
            "reminder_id": {"type": "integer"}
        },
        "required": ["reminder_id"]
    },
    risk_level=RiskLevel.DESTRUCTIVE,
    requires_confirmation=False
)
def handle_delete_reminder(reminder_id: int, session_id: str = "default"):
    delete_reminder(session_id=session_id, reminder_id=reminder_id)
    return {"reminder_id": reminder_id, "status": "deleted"}

from app.memory.memory_manager import add_memory, list_memories as list_mem_db, deactivate_memory

@register_tool(
    name="remember_information",
    description="Save a useful fact, preference, context, or project detail to persistent AI memory. Use this when the user explicitly asks you to remember something.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The information to remember."},
            "category": {"type": "string", "enum": ["preference", "project", "workflow", "goal", "instruction", "context"], "description": "Category of the information."},
            "importance": {"type": "string", "enum": ["high", "medium", "low"], "description": "Importance level."}
        },
        "required": ["content"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def remember_information_tool(content: str, category: str = "preference", importance: str = "medium") -> str:
    result = add_memory(content, category, importance)
    return result["message"]

@register_tool(
    name="list_memories",
    description="List all active persistent memories stored by the assistant.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def list_memories_tool() -> str:
    memories = list_mem_db()
    if not memories:
        return "No active memories found."
    output = "Stored Memories:\n"
    for m in memories:
        output += f"- [{m['category'].upper()}] {m['content']} (Importance: {m['importance']})\n"
    return output

@register_tool(
    name="forget_information",
    description="Deactivate or forget a previously saved memory.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The information or topic to forget."}
        },
        "required": ["content"]
    },
    risk_level=RiskLevel.DESTRUCTIVE,
    requires_confirmation=False
)
def forget_information_tool(content: str) -> str:
    result = deactivate_memory(content)
    return result["message"]

from app.planning.planning_manager import create_goal, list_goals, create_project_plan as db_create_plan, create_milestone, create_plan_task, get_active_tasks, add_task_dependency
from app.planning.planning_service import generate_plan
from app.planning.progress_tracker import detect_overdue_tasks
from app.planning.prioritizer import suggest_next_best_action

@register_tool(
    name="create_goal",
    description="Create a high-level goal that the user wants to achieve.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"}
        },
        "required": ["title"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_goal(title: str, description: str = None):
    gid = create_goal(title, description)
    return f"Goal created with ID {gid}"

@register_tool(
    name="create_project_plan",
    description="Generate and save a structured project plan with milestones and tasks from a goal.",
    input_schema={
        "type": "object",
        "properties": {
            "goal_title": {"type": "string"},
            "goal_id": {"type": "integer"}
        },
        "required": ["goal_title"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_project_plan(goal_title: str, goal_id: int = None):
    plan_data = generate_plan(goal_title)
    pid = db_create_plan(goal_id, plan_data["title"], plan_data.get("description"))

    for m in plan_data.get("milestones", []):
        mid = create_milestone(pid, m["title"], m.get("description"))
        for t in m.get("tasks", []):
            create_plan_task(mid, t["title"], t.get("description"), t.get("priority", "medium"), t.get("estimated_minutes", 60))

    return f"Successfully created Project Plan: {plan_data.get('title')} with tasks!"

@register_tool(
    name="get_next_action",
    description="Suggest the next best actionable task across all projects.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_next_action():
    from app.database.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task_dependencies")
    deps = [dict(r) for r in cursor.fetchall()]
    conn.close()

    tasks = get_active_tasks()
    best = suggest_next_best_action(tasks, deps)
    if best:
        return f"Next Best Action: {best['title']} (Priority: {best.get('priority', 'medium')})"
    return "No actionable tasks available right now."

@register_tool(
    name="detect_overdue_tasks",
    description="Detect overdue tasks in project plans.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_detect_overdue():
    tasks = get_active_tasks()
    overdue = detect_overdue_tasks(tasks)
    if not overdue:
        return "You have no overdue tasks!"
    return f"You have {len(overdue)} overdue tasks: " + ", ".join(t["title"] for t in overdue)

from app.analytics.report_generator import get_productivity_summary, generate_weekly_report
import json

@register_tool(
    name="get_productivity_summary",
    description="Get the overall productivity summary, including completion rates and priority breakdowns.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_productivity_summary():
    summary = get_productivity_summary()
    return f"Productivity Score: {summary.productivity_score:.1f}/100. Completion Rate: {summary.tasks.completion_rate:.1f}%. Overdue: {summary.tasks.overdue_tasks}."

@register_tool(
    name="get_task_metrics",
    description="Get the total count of completed, pending, and overdue tasks.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_task_metrics():
    from app.analytics.metrics import get_task_metrics as gtm
    m = gtm()
    return f"Tasks: {m.total_tasks} total, {m.completed_tasks} completed, {m.pending_tasks} pending, {m.overdue_tasks} overdue."

@register_tool(
    name="get_completion_trends",
    description="Compare task completion this week vs last week.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_completion_trends():
    from app.analytics.trends import get_weekly_comparison
    comp = get_weekly_comparison()
    if not comp:
        return "Not enough data for a weekly comparison."
    return f"This week: {comp['this_week']} completed. Last week: {comp['previous_week']} completed. Change: {comp['change_percentage']:.1f}%."

@register_tool(
    name="generate_weekly_report",
    description="Generate a detailed weekly productivity report.",
    input_schema={"type": "object", "properties": {}},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_generate_weekly_report():
    report = generate_weekly_report()
    return json.dumps(report)

from app.web_tools.url_validator import validate_url, get_official_url


from app.web_tools.web_search import perform_web_search, WebSearchRequest
from urllib.parse import quote_plus

@register_tool(
    name="validate_url",
    description="Validates if a URL is safe and well-formed (http/https).",
    input_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_validate_url(url: str):
    is_valid = validate_url(url)
    return f"URL '{url}' is valid: {is_valid}"

@register_tool(
    name="search_web",
    description="Searches the web for the given query.",
    input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_search_web(query: str):
    req = WebSearchRequest(query=query)
    resp = perform_web_search(req)
    if not resp.success:
        return resp.message
    # Return formatted results if any
    lines = [f"Results for '{query}':"]
    for r in resp.results:
        lines.append(f"- {r.title}: {r.url}\n  {r.snippet}")
    return "\n".join(lines)


from app.web_tools.system_tools import close_application, open_window, close_window, focus_application, switch_application
from app.web_tools.browser_tools import open_website, close_browser, search_google, search_youtube
from app.web_tools.media_tools import play_media, pause_media, resume_media, stop_media, volume_up, volume_down, mute

@register_tool(
    name='close_application',
    description='Closes a local desktop application by name.',
    input_schema={'type': 'object', 'properties': {'app_name': {'type': 'string'}}, 'required': ['app_name']},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_close_application(app_name: str):
    return close_application(app_name)

@register_tool(
    name='search_google',
    description='Searches Google for the given query in the browser.',
    input_schema={'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_search_google(query: str):
    return search_google(query)

@register_tool(
    name='search_youtube',
    description='Searches YouTube for the given query in the browser.',
    input_schema={'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_search_youtube(query: str):
    return search_youtube(query)

@register_tool(
    name='close_browser',
    description='Closes all known browser instances forcefully but safely.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_close_browser():
    return close_browser()

@register_tool(
    name='play_media',
    description='Plays media. If a query is given, it searches YouTube and plays it. If no query, just presses play.',
    input_schema={'type': 'object', 'properties': {'query': {'type': 'string'}}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_play_media(query: str = None):
    return play_media(query)

@register_tool(
    name='pause_media',
    description='Pauses the currently playing media.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_pause_media():
    return pause_media()

@register_tool(
    name='resume_media',
    description='Resumes the currently paused media.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_resume_media():
    return resume_media()

@register_tool(
    name='stop_media',
    description='Stops the currently playing media.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_stop_media():
    return stop_media()

@register_tool(
    name='volume_up',
    description='Increases the system volume.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_volume_up():
    return volume_up()

@register_tool(
    name='volume_down',
    description='Decreases the system volume.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_volume_down():
    return volume_down()

@register_tool(
    name='mute',
    description='Mutes the system volume.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_mute():
    return mute()

@register_tool(
    name='open_window',
    description='Opens the most recent window (switch application).',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_open_window():
    return open_window()

@register_tool(
    name='close_window',
    description='Closes the active window using Alt+F4.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_close_window():
    return close_window()

@register_tool(
    name='focus_application',
    description='Brings the specified application to focus.',
    input_schema={'type': 'object', 'properties': {'app_name': {'type': 'string'}}, 'required': ['app_name']},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_focus_application(app_name: str):
    return focus_application(app_name)

@register_tool(
    name='switch_application',
    description='Switches to the last active application using Alt+Tab.',
    input_schema={'type': 'object', 'properties': {}},
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_switch_application():
    return switch_application()






@register_tool(
    name="open_application",
    description="Opens a local desktop application by name (e.g., vs code, notepad, calculator).",
    input_schema={
        "type": "object",
        "properties": {
            "app_name": {"type": "string"}
        },
        "required": ["app_name"]
    },
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_open_application(app_name: str):
    return open_application(app_name)

@register_tool(
    name="open_website",
    description="Opens a given website URL in the browser.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string"}
        },
        "required": ["url"]
    },
    risk_level=RiskLevel.EXTERNAL,
    requires_confirmation=False
)
def handle_open_website(url: str):
    return open_website(url)

import app.agent.file_tools
import app.agent.system_info_tools
