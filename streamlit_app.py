import streamlit as st
import requests
from datetime import datetime

from app.tasks.task_manager import (
    get_tasks,
    complete_task,
    delete_task
)

from app.reminders.reminder_manager import (
    get_reminders,
    complete_reminder,
    delete_reminder
)

from app.ai.assistant import (
    get_chat_history
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Productivity Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 750;
        margin-bottom: 2px;
    }

    .subtitle {
        font-size: 17px;
        opacity: 0.75;
        margin-bottom: 15px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .user-message {
        padding: 14px;
        border-radius: 12px;
        margin-top: 8px;
        margin-bottom: 6px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    .assistant-message {
        padding: 14px;
        border-radius: 12px;
        margin-bottom: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## 🤖 AI Assistant"
    )

    st.caption(
        "Intelligent Productivity Platform"
    )

    st.divider()

    st.markdown(
        "### Navigation"
    )

    page = st.radio(
        "Go to",
        [
            "🏠 Dashboard",
            "💬 AI Assistant",
            "📋 Tasks",
            "⏰ Reminders",
            "📜 Chat History",
            "ℹ️ About"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown(
        "### System"
    )

    st.success(
        "● Assistant Online"
    )

    st.caption(
        "FastAPI + SQLite + Gemini"
    )


# =========================================================
# LOAD DATA
# =========================================================

tasks = get_tasks()

pending_tasks = get_tasks(
    "pending"
)

reminders = get_reminders()

pending_reminders = get_reminders(
    "pending"
)

history = get_chat_history(
    limit=50
)


# =========================================================
# GLOBAL DATE AND TIME
# =========================================================

now = datetime.now()

current_date = now.strftime(
    "%Y-%m-%d"
)

current_time = now.strftime(
    "%H:%M"
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">'
        '🤖 AI Productivity Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Understand • Plan • Remind • Achieve'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    # -----------------------------------------------------
    # DUE REMINDERS
    # -----------------------------------------------------

    due_reminders = []

    for reminder in pending_reminders:

        reminder_date = reminder[
            "reminder_date"
        ]

        reminder_time = reminder[
            "reminder_time"
        ]

        if (
            reminder_date == current_date
            and reminder_time <= current_time
        ):

            due_reminders.append(
                reminder
            )


    if due_reminders:

        st.markdown(
            '<div class="section-title">'
            '🔔 Notifications'
            '</div>',
            unsafe_allow_html=True
        )

        for reminder in due_reminders:

            st.warning(
                f"🔔 Reminder due now: "
                f"**{reminder['title']}**"
            )

        st.divider()


    # -----------------------------------------------------
    # PRODUCTIVITY OVERVIEW
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '📊 Productivity Overview'
        '</div>',
        unsafe_allow_html=True
    )

    completed_tasks_count = len(tasks) - len(pending_tasks)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tasks", len(tasks))

    with col2:
        st.metric("Pending Tasks", len(pending_tasks))

    with col3:
        st.metric("Completed Tasks", completed_tasks_count)

    with col4:
        st.metric("Upcoming Reminders", len(pending_reminders))

    with col5:
        st.metric("Recent Conversations", len(history))

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🔔 Notifications & Status'
        '</div>',
        unsafe_allow_html=True
    )

    col_notif, col_status = st.columns(2)

    with col_notif:
        st.write("**Notifications**")
        has_notification = False
        if pending_reminders:
            for reminder in pending_reminders:
                if reminder["reminder_date"] < current_date or (reminder["reminder_date"] == current_date and reminder["reminder_time"] <= current_time):
                    st.warning(f"⏰ **{reminder['title']}** is due!")
                    has_notification = True
        
        if not has_notification:
            st.info("No new notifications.")

    with col_status:
        st.write("**Assistant Status**")
        st.success("🟢 **Online** - Backend Connected")
        st.caption("All systems operational. Local SQLite database and natural language engine are active.")


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "💬 AI Assistant":

    st.markdown(
        '<div class="main-title">'
        '💬 AI Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Give instructions using natural language'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    st.info(
        """
        **Try commands like:**

        • Add a high priority task to finish my resume tomorrow

        • Remind me to apply for internships tomorrow at 10 AM

        • Show my pending tasks

        • Show my reminders

        • Search my documents for work from home policy
        """
    )


    message = st.text_input(
        "Your request",
        placeholder=(
            "What would you like me to do?"
        )
    )


    send_button = st.button(
        "🚀 Send Request",
        type="primary"
    )


    if send_button:

        if not message.strip():

            st.warning(
                "Please enter a message."
            )

        else:

            try:

                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={
                        "message": message
                    },
                    timeout=10
                )


                if response.status_code == 200:

                    result = response.json()

                    if result.get("success"):
                        st.success(
                            result.get(
                                "message",
                                "Request completed."
                            )
                        )
                    else:
                        st.warning(
                            result.get(
                                "message",
                                "Request failed."
                            )
                        )


                    intent = result.get(
                        "intent"
                    )


                    if intent:

                        st.caption(
                            f"Detected intent: "
                            f"`{intent}`"
                        )


                    if intent == "document_search":

                        source = result.get(
                            "source"
                        )

                        relevance_score = (
                            result.get(
                                "relevance_score"
                            )
                        )


                        if source:

                            st.info(
                                f"📄 Source: {source}"
                            )


                        if (
                            relevance_score
                            is not None
                        ):

                            st.caption(
                                f"🎯 Relevance score: "
                                f"{relevance_score}"
                            )


                    if intent in {

                        "create_task",

                        "complete_task",

                        "delete_task",

                        "create_reminder",

                        "delete_reminder"

                    }:

                        st.rerun()


                else:

                    st.error(
                        f"Backend returned "
                        f"status {response.status_code}"
                    )


            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to FastAPI. "
                    "Make sure Uvicorn is running "
                    "on port 8000."
                )


            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. "
                    "Please try again."
                )


            except Exception as error:

                st.error(
                    f"Unexpected error: {error}"
                )


# =========================================================
# TASKS
# =========================================================

elif page == "📋 Tasks":

    st.markdown(
        '<div class="main-title">'
        '📋 Task Management'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Manage your tasks and priorities'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    if pending_tasks:

        for task in pending_tasks:

            col1, col2, col3 = st.columns(
                [6, 2, 2]
            )


            with col1:

                st.write(
                    f"**{task['id']}. "
                    f"{task['title']}**"
                )

                details = (
                    f"Priority: "
                    f"{task['priority']}"
                )

                if task["due_date"]:

                    details += (
                        f" | Due: "
                        f"{task['due_date']}"
                    )

                st.caption(
                    details
                )


            with col2:

                if st.button(
                    "✅ Complete",
                    key=f"task_complete_{task['id']}"
                ):

                    complete_task(
                        task["id"]
                    )

                    st.rerun()


            with col3:

                if st.button(
                    "🗑️ Delete",
                    key=f"task_delete_{task['id']}"
                ):

                    delete_task(
                        task["id"]
                    )

                    st.rerun()


            st.divider()

    else:

        st.success(
            "🎉 No pending tasks."
        )


# =========================================================
# REMINDERS
# =========================================================

elif page == "⏰ Reminders":

    st.markdown(
        '<div class="main-title">'
        '⏰ Reminder Management'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Keep track of important events'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    st.info(
        f"Current system time: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )


    if pending_reminders:

        for reminder in pending_reminders:

            reminder_date = (
                reminder["reminder_date"]
            )

            reminder_time = (
                reminder["reminder_time"]
            )


            is_due = (
                reminder_date == current_date
                and reminder_time <= current_time
            )


            col1, col2, col3 = st.columns(
                [6, 2, 2]
            )


            # ---------------------------------------------
            # REMINDER INFORMATION
            # ---------------------------------------------

            with col1:

                if is_due:

                    st.warning(
                        f"🔔 **{reminder['title']}**"
                    )

                    st.caption(
                        f"Due: "
                        f"{reminder_date} "
                        f"at "
                        f"{reminder_time}"
                    )

                else:

                    st.write(
                        f"⏰ **{reminder['title']}**"
                    )

                    st.caption(
                        f"Scheduled: "
                        f"{reminder_date} "
                        f"at "
                        f"{reminder_time}"
                    )


            # ---------------------------------------------
            # COMPLETE BUTTON
            # ---------------------------------------------

            with col2:

                if st.button(
                    "✅ Complete",
                    key=f"reminder_complete_{reminder['id']}"
                ):

                    complete_reminder(
                        reminder["id"]
                    )

                    st.rerun()


            # ---------------------------------------------
            # DELETE BUTTON
            # ---------------------------------------------

            with col3:

                if st.button(
                    "🗑️ Delete",
                    key=f"reminder_delete_{reminder['id']}"
                ):

                    delete_reminder(
                        reminder["id"]
                    )

                    st.rerun()


            st.divider()


    else:

        st.success(
            "🎉 No pending reminders."
        )


# =========================================================
# CHAT HISTORY
# =========================================================

elif page == "📜 Chat History":

    st.markdown(
        '<div class="main-title">'
        '📜 Chat History'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Review previous interactions with your assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    if history:

        st.caption(
            f"Showing {len(history)} recent conversations"
        )


        for chat in history:

            st.markdown(
                f"""
                <div class="user-message">
                <strong>👤 You</strong><br><br>
                {chat["user_message"]}
                </div>
                """,
                unsafe_allow_html=True
            )


            st.markdown(
                f"""
                <div class="assistant-message">
                <strong>🤖 Assistant</strong><br><br>
                {chat["assistant_response"]}
                </div>
                """,
                unsafe_allow_html=True
            )


            st.caption(
                f"🕒 {chat['created_at']}"
            )


            st.divider()


    else:

        st.info(
            "No chat history available yet."
        )


# =========================================================
# ABOUT
# =========================================================

elif page == "ℹ️ About":

    st.markdown(
        '<div class="main-title">'
        'ℹ️ About the Project'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Intelligent AI Productivity Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    st.markdown(
        """
        ### 🤖 Intelligent AI Productivity Assistant

        A Python-based AI productivity platform that understands
        natural-language requests and executes actions through
        specialized application tools.

        ### Core Features

        **🧠 AI Assistant**
        - Natural-language understanding
        - Gemini-powered responses
        - Intent detection
        - Tool-based action execution

        **📋 Task Management**
        - Create tasks
        - Task priorities
        - Due dates
        - Complete tasks
        - Delete tasks

        **⏰ Reminder System**
        - Natural-language reminders
        - Date and time extraction
        - Background scheduling
        - Due reminder notifications
        - Complete reminders
        - Delete reminders

        **📄 Document Intelligence**
        - Document search
        - Context-based question answering
        - Source identification
        - Relevance scoring

        **📜 Chat History**
        - Persistent conversation storage
        - SQLite database
        - Recent interaction history

        ### Technology Stack

        | Layer | Technology |
        |---|---|
        | Frontend | Streamlit |
        | Backend | FastAPI |
        | Language | Python |
        | Database | SQLite |
        | AI | Google Gemini |
        | Scheduler | APScheduler |
        | Documents | PyPDF / python-docx |
        | Data | Pandas |

        ### Architecture

        ```
        User
          ↓
        Streamlit Dashboard
          ↓
        FastAPI Backend
          ↓
        Intent Detection
          ↓
        Action Router
          ↓
        ┌──────────────┬──────────────┬──────────────┐
        │ Task Manager │ Reminder     │ Documents    │
        │              │ Manager      │              │
        └──────────────┴──────────────┴──────────────┘
                         ↓
                    SQLite Database
        ```
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Intelligent AI Productivity Assistant • "
    "Python • FastAPI • Streamlit • SQLite • Gemini"
)

