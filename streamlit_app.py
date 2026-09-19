import streamlit as st
import requests
from datetime import datetime
import json
from zoneinfo import ZoneInfo

from app.tasks.task_manager import get_tasks, complete_task, delete_task
from app.reminders.reminder_manager import get_reminders, complete_reminder, delete_reminder
from app.documents.document_manager import search_documents
from app.ai.assistant import get_chat_history

INDIA_TZ = ZoneInfo("Asia/Kolkata")

st.set_page_config(
    page_title="Intelligent AI Productivity Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS = """
<style>
    :root {
        --bg: #0B0F14;
        --surface-1: #111827;
        --surface-2: #151B23;
        --border: #1F2937;

        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #94A3B8;
        --text-subtle: #64748B;

        --accent: #3B82F6;
        --success: #22C55E;
        --warning: #F59E0B;
        --error: #EF4444;

        --radius: 6px;
        --transition: all 0.2s ease-in-out;
    }

    [data-testid="stAppViewContainer"] { background-color: var(--bg) !important; }
    [data-testid="stSidebar"] { background-color: var(--surface-1) !important; border-right: 1px solid var(--border); }
    [data-testid="stHeader"] { background-color: var(--bg) !important; }

    h1, h2, h3, h4, h5, h6, p, span, div, label {
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        color: var(--text-primary);
    }

    .page-title { font-size: 28px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
    .page-subtitle { font-size: 15px; color: var(--text-muted); margin-bottom: 32px; }
    .section-title { font-size: 18px; font-weight: 600; color: var(--text-primary); margin: 32px 0 16px 0; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

    .metric-card { background-color: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
    .metric-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); font-weight: 600; margin-bottom: 8px; }
    .metric-value { font-size: 32px; font-weight: 700; line-height: 1.2; color: var(--text-primary); margin-bottom: 4px; }

    .data-row { background-color: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .data-row-main { flex: 1; }
    .data-row-title { font-size: 14px; font-weight: 500; color: var(--text-primary); margin-bottom: 2px; }
    .data-row-meta { font-size: 12px; color: var(--text-muted); }
    .data-row-side { display: flex; gap: 8px; align-items: center; }

    .badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid var(--border); background-color: var(--surface-1); display: inline-flex; align-items: center; justify-content: center; }
    .badge-high { color: var(--error); border-color: rgba(239, 68, 68, 0.3); }
    .badge-medium { color: var(--warning); border-color: rgba(245, 158, 11, 0.3); }
    .badge-low { color: var(--success); border-color: rgba(34, 197, 94, 0.3); }
    .badge-pending { color: var(--accent); border-color: rgba(59, 130, 246, 0.3); }
    .badge-completed { color: var(--success); border-color: rgba(34, 197, 94, 0.3); }

    .chat-card { background-color: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; }
    .chat-role { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-subtle); margin-bottom: 8px; }
    .chat-role.user { color: var(--accent); }
    .chat-content { font-size: 14px; line-height: 1.5; }
    .chat-content.user { color: var(--text-primary); }
    .chat-content.assistant { color: var(--text-secondary); }

    .empty-state { text-align: center; padding: 48px 16px; background-color: var(--surface-2); border-radius: var(--radius); border: 1px dashed var(--border); margin: 16px 0; }
    .empty-state-title { font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 4px; }

    div[data-testid="stButton"] button { border-radius: var(--radius); border: 1px solid var(--border); background-color: var(--surface-2); color: var(--text-secondary); font-weight: 500; font-size: 13px; padding: 4px 12px; transition: var(--transition); }
    div[data-testid="stButton"] button:hover { border-color: var(--text-subtle); background-color: var(--surface-1); color: var(--text-primary); }
    div[data-testid="stButton"] button[kind="primary"] { background-color: var(--accent); color: #FFFFFF; border: none; }

    .sidebar-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-primary); margin-bottom: 4px; line-height: 1.4; }
    .sidebar-subtitle { font-size: 12px; color: var(--text-muted); margin-bottom: 32px; }
    .sidebar-footer { font-size: 12px; color: var(--text-subtle); margin-top: 32px; }

    #MainMenu, footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def render_metric_card(label, value):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

def render_status_badge(text, status_type):
    return f'<span class="badge badge-{status_type}">{text}</span>'

def render_task_row(task):
    priority = task.get('priority', 'low').lower()
    p_badge = render_status_badge(priority, priority)
    status = task.get('status', 'pending').lower()
    s_badge = render_status_badge(status, status)
    due = f"Due: {task.get('due_date')}" if task.get('due_date') else "No due date"
    st.markdown(f'<div class="data-row"><div class="data-row-main"><div class="data-row-title">{task.get("title", "")}</div><div class="data-row-meta">ID: {task.get("id", "")} &bull; {due}</div></div><div class="data-row-side">{s_badge}{p_badge}</div></div>', unsafe_allow_html=True)

def format_ist_datetime(date_str, time_str=None):
    try:
        if time_str:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            return dt.strftime("%d %b %Y • %I:%M %p") + " IST"
        else:
            # Handle ISO timestamp
            dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if "T" in date_str else datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
            dt_ist = dt_utc.astimezone(INDIA_TZ)
            return dt_ist.strftime("%d %b %Y • %I:%M %p") + " IST"
    except Exception:
        return f"{date_str} {time_str if time_str else ''} IST"

def render_reminder_row(r, is_due):
    s_class = "pending" if is_due else "low"
    s_text = r.get("status", "Pending").capitalize()
    if s_text.lower() == "completed": s_class = "completed"
    s_badge = render_status_badge(s_text, s_class)
    formatted_dt = format_ist_datetime(r.get('reminder_date', ''), r.get('reminder_time', ''))
    st.markdown(f'<div class="data-row"><div class="data-row-main"><div class="data-row-title">{r.get("title", "")}</div><div class="data-row-meta">{formatted_dt}</div></div><div class="data-row-side">{s_badge}</div></div>', unsafe_allow_html=True)

def render_section_header(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def render_empty_state(title):
    st.markdown(f'<div class="empty-state"><div class="empty-state-title">{title}</div></div>', unsafe_allow_html=True)

def render_chat_message(role, content, metadata=None):
    role_class = role.lower()
    meta_html = ""
    if metadata and metadata.get("tool"):
        tool_name = metadata.get("tool")
        status = metadata.get("status", "")
        duration = metadata.get("duration", "")
        meta_html = f'<div style="margin-top: 12px; padding: 8px; background: var(--surface-1); border-radius: 4px; border: 1px solid var(--border); font-size: 12px; color: var(--text-muted);"><strong>Agent Plan Executed</strong><br>Tool: {tool_name}<br>Status: {status}<br>Duration: {duration}</div>'

    st.markdown(f'<div class="chat-card"><div class="chat-role {role_class}">{role}</div><div class="chat-content {role_class}">{content}{meta_html}</div></div>', unsafe_allow_html=True)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Overview"

tasks_raw = get_tasks()
pending_tasks_raw = get_tasks("pending")
reminders_raw = get_reminders()
pending_reminders_raw = get_reminders("pending")
history_raw = get_chat_history(limit=50)

tasks = [dict(t) for t in tasks_raw]
pending_tasks = [dict(t) for t in pending_tasks_raw]
reminders = [dict(r) for r in reminders_raw]
pending_reminders = [dict(r) for r in pending_reminders_raw]
history = [dict(h) for h in history_raw]

completed_tasks_count = len(tasks) - len(pending_tasks)
now = datetime.now(INDIA_TZ)
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M")

with st.sidebar:
    st.markdown('<div class="sidebar-title">INTELLIGENT AI<br>PRODUCTIVITY<br>ASSISTANT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Productivity workspace</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size: 11px; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; margin: 16px 0 8px 0;">Workspace</div>', unsafe_allow_html=True)
    for p in ["Overview", "My Tasks", "Reminders", "Documents"]:
        if st.button(p, use_container_width=True, type="primary" if st.session_state.current_page == p else "secondary"): st.session_state.current_page = p

    st.markdown('<div style="font-size: 11px; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; margin: 16px 0 8px 0;">AI</div>', unsafe_allow_html=True)
    for p in ["AI Assistant", "Voice Assistant", "Memory", "Planning", "Analytics"]:
        if st.button(p, use_container_width=True, type="primary" if st.session_state.current_page == p else "secondary"): st.session_state.current_page = p

    st.markdown('<div style="font-size: 11px; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; margin: 16px 0 8px 0;">Activity & System</div>', unsafe_allow_html=True)
    for p in ["Chat History", "Security / Activity", "About"]:
        if st.button(p, use_container_width=True, type="primary" if st.session_state.current_page == p else "secondary"): st.session_state.current_page = p

    st.markdown('<div class="sidebar-footer">Version 1.0</div>', unsafe_allow_html=True)

page = st.session_state.current_page

if page == "Overview":
    st.markdown('<div class="page-title">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your centralized productivity workspace.</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: render_metric_card("Pending Tasks", len(pending_tasks))
    with col2: render_metric_card("Completed Tasks", completed_tasks_count)
    with col3: render_metric_card("Upcoming Reminders", len(pending_reminders))
    with col4: render_metric_card("Conversations", len(history))

    render_section_header("Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("Create Task", use_container_width=True): st.session_state.current_page = "AI Assistant"; st.rerun()
    with qa2:
        if st.button("Create Reminder", use_container_width=True): st.session_state.current_page = "AI Assistant"; st.rerun()
    with qa3:
        if st.button("Ask AI", use_container_width=True): st.session_state.current_page = "AI Assistant"; st.rerun()
    with qa4:
        if st.button("View Tasks", use_container_width=True): st.session_state.current_page = "My Tasks"; st.rerun()

    col_main, col_side = st.columns([2, 1])
    with col_main:
        render_section_header("Upcoming Reminders")
        if pending_reminders:
            for r in pending_reminders[:5]:
                is_due = (r["reminder_date"] < current_date) or (r["reminder_date"] == current_date and r["reminder_time"] <= current_time)
                render_reminder_row(r, is_due)
        else:
            render_empty_state("No reminders scheduled.")

        render_section_header("Recent Activity")
        if history:
            for h in history[:5]:
                ts = format_ist_datetime(h.get('created_at', ''))
                st.markdown(f'<div class="data-row"><div class="data-row-main"><div class="data-row-title">Conversation recorded</div></div><div class="data-row-side"><span style="font-size: 12px; color: var(--text-muted);">{ts}</span></div></div>', unsafe_allow_html=True)
        else:
            render_empty_state("No recent activity.")

    with col_side:
        render_section_header("Productivity Snapshot")
        st.markdown(f"""<div class="metric-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; color: var(--text-muted);">Pending Tasks</span>
                <span style="font-size: 13px; color: var(--text-primary); font-weight: 600;">{len(pending_tasks)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; color: var(--text-muted);">Completed Tasks</span>
                <span style="font-size: 13px; color: var(--text-primary); font-weight: 600;">{completed_tasks_count}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; color: var(--text-muted);">Upcoming Reminders</span>
                <span style="font-size: 13px; color: var(--text-primary); font-weight: 600;">{len(pending_reminders)}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 13px; color: var(--text-muted);">Conversations</span>
                <span style="font-size: 13px; color: var(--text-primary); font-weight: 600;">{len(history)}</span>
            </div>
        </div>""", unsafe_allow_html=True)

elif page == "AI Assistant":
    st.markdown('<div class="page-title">AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Ask questions or manage your productivity using natural language.</div>', unsafe_allow_html=True)

    if "session_messages" not in st.session_state:
        st.session_state.session_messages = [{"role": "ASSISTANT", "content": "How can I help you manage your workspace today?"}]

    for message in st.session_state.session_messages:
        render_chat_message(message["role"], message["content"], message.get("metadata"))

    if prompt := st.chat_input("Enter natural language command..."):
        st.session_state.session_messages.append({"role": "USER", "content": prompt})
        render_chat_message("USER", prompt)
        with st.spinner("Processing..."):
            try:
                response = requests.post("http://127.0.0.1:8000/chat", json={"message": prompt}, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("message", "Request completed successfully.")
                    if "limit has been reached" in reply.lower() or "quota" in reply.lower():
                        reply = "AI usage limit reached. Productivity features remain available."
                    st.session_state.session_messages.append({"role": "ASSISTANT", "content": reply, "metadata": data})
                elif response.status_code == 429:
                    st.session_state.session_messages.append({"role": "ASSISTANT", "content": "AI usage limit reached. Productivity features remain available."})
                else:
                    st.session_state.session_messages.append({"role": "ASSISTANT", "content": "Application backend is unavailable. Please start the FastAPI server."})
            except Exception as e:
                st.session_state.session_messages.append({"role": "ASSISTANT", "content": "Application backend is unavailable. Please start the FastAPI server."})
                with st.expander("Technical details"):
                    st.code(str(e))
            st.rerun()

elif page == "My Tasks":
    st.markdown('<div class="page-title">My Tasks</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage your work and priorities.</div>', unsafe_allow_html=True)
    if pending_tasks:
        for task in pending_tasks:
            col_data, col_btn1, col_btn2 = st.columns([8, 1, 1])
            with col_data: render_task_row(task)
            with col_btn1:
                if st.button("Complete", key=f"tc_{task.get('id')}", use_container_width=True): complete_task(task.get('id')); st.rerun()
            with col_btn2:
                if st.button("Delete", key=f"td_{task.get('id')}", use_container_width=True): delete_task(task.get('id')); st.rerun()
    else:
        render_empty_state("No tasks found.")

elif page == "Reminders":
    st.markdown('<div class="page-title">Reminders</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Keep track of scheduled activities.</div>', unsafe_allow_html=True)
    if pending_reminders:
        for r in pending_reminders:
            is_due = (r.get("reminder_date", "") < current_date) or (r.get("reminder_date", "") == current_date and r.get("reminder_time", "") <= current_time)
            col_data, col_btn1, col_btn2 = st.columns([8, 1, 1])
            with col_data: render_reminder_row(r, is_due)
            with col_btn1:
                if st.button("Complete", key=f"rc_{r.get('id')}", use_container_width=True): complete_reminder(r.get('id')); st.rerun()
            with col_btn2:
                if st.button("Delete", key=f"rd_{r.get('id')}", use_container_width=True): delete_reminder(r.get('id')); st.rerun()
    else:
        render_empty_state("No reminders scheduled.")

elif page == "Documents":
    st.markdown('<div class="page-title">Semantic RAG Document Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Search your documents using advanced semantic hybrid retrieval and get AI-grounded answers.</div>', unsafe_allow_html=True)

    from app.documents.document_manager import get_indexed_documents, index_all_documents, search_documents
    import os
    from pathlib import Path

    DOCUMENTS_DIR = Path("documents")

    # --- Upload ---
    uploaded_file = st.file_uploader("Upload Document (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        if st.button("Save & Index"):
            DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
            file_path = DOCUMENTS_DIR / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            with st.spinner("Indexing new document..."):
                index_all_documents()
            st.success(f"Saved and indexed {uploaded_file.name}")
            st.rerun()

    st.markdown("---")

    # --- Indexed Documents ---
    st.markdown('### Indexed Documents')
    docs = get_indexed_documents()

    col1, col2 = st.columns([5,1])
    with col1:
        pass
    with col2:
        if st.button("Re-index All"):
            with st.spinner("Rebuilding index..."):
                index_all_documents()
            st.success("Indexing complete.")
            st.rerun()

    if docs:
        st.markdown(
            '<div style="display: grid; grid-template-columns: 3fr 1fr 1fr 2fr 2fr; font-size: 12px; font-weight: bold; color: var(--text-muted); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 8px;">'
            '<div>Filename</div><div>Type</div><div>Chunks</div><div>Status</div><div>Last Indexed</div></div>',
            unsafe_allow_html=True
        )
        for d in docs:
            st.markdown(
                f'<div style="display: grid; grid-template-columns: 3fr 1fr 1fr 2fr 2fr; font-size: 13px; color: var(--text-secondary); padding: 8px 0; border-bottom: 1px solid var(--border);">'
                f'<div>{d["filename"]}</div><div>{d["file_type"].upper()}</div><div>{d["chunk_count"]}</div><div>{d["status"]}</div><div>{d["indexed_at"]}</div></div>',
                unsafe_allow_html=True
            )
    else:
        render_empty_state("No documents indexed yet.")

    st.markdown("---")

    # --- Ask your documents ---
    st.markdown('### Ask your documents')
    query = st.text_input("Enter your question...", placeholder="E.g., How many days can I work from home?")
    if st.button("Search Documents", type="primary"):
        if query:
            with st.spinner("Running hybrid semantic search..."):
                results = search_documents(query)

                # Answer
                st.markdown('#### Answer')
                st.markdown(f'<div class="metric-card" style="margin-bottom: 16px;">{results.get("answer", "No answer generated.")}</div>', unsafe_allow_html=True)

                # Sources
                sources = results.get("sources", [])
                if sources:
                    st.markdown('#### Sources')
                    for src in sources:
                        st.markdown(f'- `{src}`')
                elif results.get("error"):
                    with st.expander("Technical details"):
                        st.code(results.get("error"))


elif page == "Chat History":
    st.markdown('<div class="page-title">Chat History</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Review your past interactions.</div>', unsafe_allow_html=True)
    if history:
        for chat in history:
            ts = format_ist_datetime(chat.get('created_at', ''))
            with st.expander(f"{ts} - {chat.get('user_message', '')[:40]}..."):
                render_chat_message("USER", chat.get('user_message', ''))
                render_chat_message("ASSISTANT", chat.get('assistant_response', ''))
    else:
        render_empty_state("No conversations yet.")

elif page == "Memory":
    st.markdown('<div class="page-title">AI Memory</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Persistent memories your assistant has stored about your preferences and projects.</div>', unsafe_allow_html=True)

    try:
        from app.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE active = 1 ORDER BY id DESC")
        memories = [dict(r) for r in cursor.fetchall()]
        conn.close()

        if memories:
            st.markdown(
                '<div style="display: grid; grid-template-columns: 1fr 3fr 1fr 1fr 1fr; font-size: 12px; font-weight: bold; color: var(--text-muted); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 8px;">'
                '<div>Category</div><div>Memory</div><div>Importance</div><div>Last Used</div><div>Action</div></div>',
                unsafe_allow_html=True
            )
            for m in memories:
                col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
                with col1:
                    st.markdown(f'<div style="font-size: 13px; color: var(--text-secondary);">{m.get("category", "").upper()}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div style="font-size: 13px; color: var(--text-secondary);">{m.get("content", "")}</div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div style="font-size: 13px; color: var(--text-secondary);">{m.get("importance", "")}</div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div style="font-size: 13px; color: var(--text-secondary);">{m.get("last_used_at", "-")}</div>', unsafe_allow_html=True)
                with col5:
                    if st.button("Deactivate", key=f"deactivate_{m['id']}", use_container_width=True):
                        from app.memory.memory_manager import deactivate_memory
                        deactivate_memory(m['content'])
                        st.rerun()
        else:
            render_empty_state("No active memories stored.")

    except Exception as e:
        render_empty_state(f"Error loading memories: {e}")

elif page == "Planning":
    st.markdown('<div class="page-title">Proactive AI Planning</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Turn your goals into structured projects with milestones, tasks, and dependencies.</div>', unsafe_allow_html=True)

    try:
        from app.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        # Goals
        st.subheader("🎯 Active Goals")
        cursor.execute("SELECT * FROM goals WHERE status = 'active' ORDER BY id DESC")
        goals = [dict(r) for r in cursor.fetchall()]

        if goals:
            for g in goals:
                st.markdown(f"**{g['title']}** (Priority: {g['priority']}) - Target: {g.get('target_date', 'None')}")
        else:
            render_empty_state("No active goals found.")

        st.divider()
        st.subheader("📋 Project Plans & Progress")
        cursor.execute("SELECT * FROM project_plans WHERE status = 'active' ORDER BY id DESC")
        plans = [dict(r) for r in cursor.fetchall()]

        if plans:
            from app.planning.progress_tracker import get_progress
            for p in plans:
                st.markdown(f"### {p['title']}")
                cursor.execute("SELECT id FROM milestones WHERE plan_id = ?", (p['id'],))
                m_ids = [r['id'] for r in cursor.fetchall()]

                tasks = []
                for m_id in m_ids:
                    cursor.execute("SELECT * FROM plan_tasks WHERE milestone_id = ?", (m_id,))
                    tasks.extend([dict(r) for r in cursor.fetchall()])

                progress = get_progress(tasks)
                st.progress(int(progress.completion_percentage))
                st.caption(f"{progress.completion_percentage:.1f}% Completed | {progress.pending_tasks} Pending | {progress.overdue_tasks} Overdue")

                if st.button(f"View Plan Details", key=f"view_plan_{p['id']}"):
                    st.info("Plan details view is active in the backend agent.")
        else:
            render_empty_state("No project plans yet.")

        conn.close()

        st.divider()
        st.subheader("🤖 Create AI Plan")
        with st.form("create_plan_form"):
            goal_input = st.text_input("What is your goal?")
            if st.form_submit_button("Generate Proposed Plan"):
                if goal_input:
                    with st.spinner("AI is generating a plan..."):
                        from app.planning.planning_service import generate_plan
                        plan = generate_plan(goal_input)
                        st.json(plan)
                        st.info("Use the AI Assistant chat to ask it to confirm and create this plan.")

    except Exception as e:
        render_empty_state(f"Error loading planning view: {e}")

elif page == "About":
    st.markdown('<div class="page-title">Intelligent AI Productivity Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">A Python-based productivity platform that combines natural-language interaction with task management, reminders, document search and AI-assisted responses.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        render_section_header("Project Overview")
        st.markdown('<div class="metric-card"><p>A robust backend architecture built with FastAPI driving a minimalist, developer-focused Streamlit presentation layer. Utilizes APScheduler for precision timed background jobs using IST timezone awareness, and an embedded Document Manager parsing PDFs and DOCX files. The integrated Google Gemini AI powers intent-classification and conversational AI fallback gracefully.</p></div>', unsafe_allow_html=True)
        render_section_header("Technology Stack")
        st.markdown('<div class="metric-card"><ul style="color: var(--text-secondary); line-height: 1.8; margin-bottom: 0;"><li>Python</li><li>FastAPI</li><li>Streamlit</li><li>SQLite</li><li>Gemini API</li><li>APScheduler</li><li>Pandas</li><li>pypdf</li><li>python-docx</li></ul></div>', unsafe_allow_html=True)
    with col2:
        render_section_header("Engineering Highlights")
        st.markdown('<div class="metric-card"><ul style="color: var(--text-secondary); line-height: 1.8; margin-bottom: 0;"><li>Natural-language request processing</li><li>Modular backend</li><li>Persistent SQLite storage</li><li>Reminder scheduling</li><li>Document search</li><li>Gemini integration</li><li>Graceful AI failure handling</li><li>IST timezone support</li><li>Chat history</li></ul></div>', unsafe_allow_html=True)

elif page == "Security / Activity":
    st.markdown('<div class="page-title">Tool Activity</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Monitor AI Agent tool executions.</div>', unsafe_allow_html=True)

    try:
        from app.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tool_activity ORDER BY id DESC LIMIT 50")
        activities = cursor.fetchall()
        conn.close()

        if activities:
            st.markdown(
                '<div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; font-size: 12px; font-weight: bold; color: var(--text-muted); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 8px;">'
                '<div>Time (IST)</div><div>Source</div><div>Tool</div><div>Status</div><div>Duration</div></div>',
                unsafe_allow_html=True
            )
            for a in activities:
                # format timestamp
                ts = a['timestamp']
                st.markdown(
                    f'<div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; font-size: 13px; color: var(--text-secondary); padding: 8px 0; border-bottom: 1px solid var(--border);">'
                    f'<div>{ts}</div><div>{a["source"]}</div><div>{a["tool_name"]}</div><div>{a["status"]}</div><div>{a["duration_ms"]} ms</div></div>',
                    unsafe_allow_html=True
                )
        else:
            render_empty_state("No tool activity recorded yet.")
    except Exception as e:
        render_empty_state("Could not load tool activity. Please ensure database is initialized.")

elif page == "Voice Assistant":
    st.markdown('<div class="page-title">Voice Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Speak natural-language commands and receive spoken responses.</div>', unsafe_allow_html=True)

    from app.voice.speech_to_text import listen_and_recognize
    from app.voice.text_to_speech import speak

    if "voice_status" not in st.session_state:
        st.session_state.voice_status = "READY"
    if "voice_transcript" not in st.session_state:
        st.session_state.voice_transcript = "No speech captured yet."
    if "voice_response" not in st.session_state:
        st.session_state.voice_response = "No response yet."
    if "voice_output_enabled" not in st.session_state:
        st.session_state.voice_output_enabled = True
    if "voice_error_details" not in st.session_state:
        st.session_state.voice_error_details = ""

    st.markdown(f"**Status:** {st.session_state.voice_status}")

    if st.button("Start Listening"):
        st.session_state.voice_status = "LISTENING"
        st.session_state.voice_transcript = "Listening..."
        st.session_state.voice_error_details = ""
        st.rerun()

    if st.session_state.voice_status == "LISTENING":
        success, text = listen_and_recognize()
        if not success:
            st.session_state.voice_status = "ERROR"
            st.session_state.voice_transcript = "Error capturing speech."
            st.session_state.voice_error_details = text
            st.rerun()
        else:
            st.session_state.voice_status = "PROCESSING"
            st.session_state.voice_transcript = f"You said:\n\n\"{text}\""
            st.rerun()

    if st.session_state.voice_status == "PROCESSING":
        prompt = st.session_state.voice_transcript.replace("You said:\n\n\"", "").rstrip("\"")
        try:
            import requests
            response = requests.post("http://127.0.0.1:8000/chat", json={"message": prompt, "source": "voice"}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", "Request completed successfully.")
                if "limit has been reached" in reply.lower() or "quota" in reply.lower():
                    reply = "AI usage limit reached. Productivity features remain available."
                st.session_state.voice_response = f"Assistant:\n\n{reply}"
                st.session_state.voice_status = "SPEAKING" if st.session_state.voice_output_enabled else "READY"
            elif response.status_code == 429:
                reply = "AI usage limit reached. Productivity features remain available."
                st.session_state.voice_response = f"Assistant:\n\n{reply}"
                st.session_state.voice_status = "SPEAKING" if st.session_state.voice_output_enabled else "READY"
            else:
                st.session_state.voice_status = "ERROR"
                st.session_state.voice_response = "Application backend is unavailable. Please start the FastAPI server."
        except Exception as e:
            st.session_state.voice_status = "ERROR"
            st.session_state.voice_response = "Application backend is unavailable. Please start the FastAPI server."
            st.session_state.voice_error_details = str(e)
        st.rerun()

    if st.session_state.voice_status == "SPEAKING":
        reply_text = st.session_state.voice_response.replace("Assistant:\n\n", "")
        if st.session_state.voice_output_enabled:
            speak(reply_text)
        st.session_state.voice_status = "READY"
        st.rerun()

    st.markdown("---")
    st.markdown("**Transcript**")
    st.markdown(f"```text\n{st.session_state.voice_transcript}\n```")

    st.markdown("**Assistant Response**")
    st.markdown(f"```text\n{st.session_state.voice_response}\n```")
    if st.session_state.voice_status == "ERROR" and st.session_state.voice_error_details:
        with st.expander("Technical details"):
            st.code(st.session_state.voice_error_details)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        toggle = st.checkbox("Voice Response ON", value=st.session_state.voice_output_enabled)
        if toggle != st.session_state.voice_output_enabled:
            st.session_state.voice_output_enabled = toggle
            st.rerun()
    with col2:
        if st.button("Stop Speaking"):
            from app.voice.text_to_speech import stop_speaking
            stop_speaking()
            st.session_state.voice_status = "READY"
            st.rerun()
