import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google import genai

from app.database.database import get_connection
from app.tasks.task_manager import (
    create_task,
    get_tasks,
    complete_task,
    delete_task,
)
from app.reminders.reminder_manager import (
    create_reminder,
    get_reminders,
    complete_reminder,
    delete_reminder,
    extract_reminder_title,
    extract_reminder_id,
)
from app.ai.intent import detect_intent, detect_computer_command
from app.agent.executor import execute_tool

# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

api_key = os.getenv("GEMINI_API_KEY")

client = None

if api_key:
    try:
        client = genai.Client(
            api_key=api_key
        )
    except Exception as error:
        print(
            f"Gemini client initialization failed: {error}"
        )
        client = None

GEMINI_MODEL = "gemini-3.7-flash"


# =========================================================
# CONSTANTS
# =========================================================

# =========================================================
# TASK EXTRACTION HELPERS
# =========================================================

def extract_task_title(message):
    """
    Extract task title from the user's message.
    """

    text = message.strip()

    patterns = [
        r"^(?:create|add|make)\s+(?:a\s+)?task\s+(?:to\s+)?(.+)$",
        r"^(?:create|add|make)\s+(?:a\s+)?task\s*:\s*(.+)$",
        r"^(?:task)\s*:\s*(.+)$",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()

            title = re.sub(
                r"\b(?:high|medium|low)\s+priority\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r"\b(?:today|tomorrow)\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            return title.strip(" .,:-")

    return text


def extract_task_priority(message):
    """
    Extract task priority.
    Default priority is medium.
    """

    text = message.lower()

    if re.search(
        r"\bhigh\s+priority\b",
        text
    ):
        return "high"

    if re.search(
        r"\blow\s+priority\b",
        text
    ):
        return "low"

    if re.search(
        r"\bmedium\s+priority\b",
        text
    ):
        return "medium"

    return "medium"


def extract_task_due_date(message):
    """
    Extract today/tomorrow due dates.
    """

    text = message.lower()

    today = datetime.now().date()

    if "tomorrow" in text:

        return (
            today + timedelta(days=1)
        ).isoformat()

    if "today" in text:

        return today.isoformat()

    return None


def extract_task_id(message):
    """
    Extract numeric task ID.
    """

    match = re.search(
        r"\b(?:task\s*)?#?(\d+)\b",
        message,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None

# =========================================================
# GEMINI RESPONSE
# =========================================================

def generate_gemini_response(prompt):
    """
    Generate a response using Gemini.
    Uses the Models API with the current Google GenAI SDK.
    """

    if client is None:
        return (
            None,
            "Gemini API key is not configured. "
            "Please check your .env file."
        )

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if response and getattr(
            response,
            "text",
            None
        ):

            return (
                response.text.strip(),
                None
            )

        return (
            None,
            "Gemini returned an empty response."
        )

    except Exception as error:

        return (
            None,
            f"Gemini error: {error}"
        )


# =========================================================
# CHAT HISTORY
# =========================================================

def save_chat_history(session_id, user_message, assistant_response):
    user_message = str(user_message)
    assistant_response = str(assistant_response)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT user_message, assistant_response FROM chat_history WHERE session_id=? ORDER BY id DESC LIMIT 1", (session_id,))
    last_record = cursor.fetchone()

    if last_record:
        if last_record["user_message"] == user_message and last_record["assistant_response"] == assistant_response:
            connection.close()
            return

    cursor.execute("INSERT INTO chat_history (session_id, user_message, assistant_response) VALUES (?, ?, ?)", (session_id, user_message, assistant_response))
    connection.commit()
    connection.close()

def get_chat_history(session_id, limit=50):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM chat_history WHERE session_id=? ORDER BY created_at DESC LIMIT ?", (session_id, limit)
    )

    history = cursor.fetchall()

    connection.close()

    return history


# REMINDER DATE/TIME EXTRACTION
# =========================================================

def extract_reminder_datetime(message):

    now = datetime.now()

    text = message.lower().strip()

    if "tomorrow" in text:

        reminder_date = (
            now.date()
            + timedelta(days=1)
        )

    else:

        reminder_date = now.date()

    reminder_time = "10:00"

    time_match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        text
    )

    if time_match:

        hour = int(
            time_match.group(1)
        )

        minute = int(
            time_match.group(2)
        )

        reminder_time = (
            f"{hour:02d}:{minute:02d}"
        )

        return (
            reminder_date.isoformat(),
            reminder_time
        )

    am_pm_match = re.search(
        r"\b(1[0-2]|0?[1-9])"
        r"(?:\s*:\s*([0-5]\d))?"
        r"\s*(am|pm)\b",
        text
    )

    if am_pm_match:

        hour = int(
            am_pm_match.group(1)
        )

        minute = (
            int(am_pm_match.group(2))
            if am_pm_match.group(2)
            else 0
        )

        period = am_pm_match.group(3)

        if period == "pm" and hour != 12:

            hour += 12

        elif period == "am" and hour == 12:

            hour = 0

        reminder_time = (
            f"{hour:02d}:{minute:02d}"
        )

    return (
        reminder_date.isoformat(),
        reminder_time
    )


# =========================================================
# MAIN MESSAGE PROCESSOR
# =========================================================

def process_message(message, session_id="default"):

    message = str(message).strip()

    cmd_info = detect_computer_command(message)
    if cmd_info:
        from app.agent.tool_registry import get_tool
        if get_tool(cmd_info["tool_name"]):
            tool_name = cmd_info["tool_name"]
            arguments = cmd_info["arguments"]
            
            # We need to execute the tool
            result = execute_tool(tool_name, arguments, session_id=session_id)
            
            response = {
                "intent": tool_name,
                "success": result.success,
                "message": result.message if result.success else f"Execution failed: {result.error or result.message}"
            }
            
            save_chat_history(session_id, message, response["message"])
            return response

    intent = detect_intent(message)


    # =====================================================
    # CREATE TASK
    # =====================================================

    if intent == "create_task":

        title = extract_task_title(message)

        priority = extract_task_priority(
            message
        )

        due_date = extract_task_due_date(
            message
        )

        task_id = create_task(
            title=title,
            priority=priority,
            due_date=due_date
        )

        due_text = ""

        if due_date:

            due_text = (
                f" Due: {due_date}."
            )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Task '{title}' created "
                f"successfully with "
                f"{priority} priority."
                f"{due_text}"
            ),

            "task_id": task_id,

            "priority": priority,

            "due_date": due_date
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # LIST TASKS
    # =====================================================

    if intent == "list_tasks":

        tasks = get_tasks(
            "pending"
        )

        if not tasks:

            response = {

                "intent": intent,

                "success": True,

                "message": (
                    "You currently have "
                    "no pending tasks."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        task_list = []

        for task in tasks:

            due_text = ""

            if task["due_date"]:

                due_text = (
                    f" | Due: "
                    f"{task['due_date']}"
                )

            task_list.append(
                f"{task['id']}. "
                f"{task['title']} "
                f"(Priority: "
                f"{task['priority']}"
                f"{due_text})"
            )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                "Your pending tasks:\n"
                + "\n".join(task_list)
            )
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # COMPLETE TASK
    # =====================================================

    if intent == "complete_task":

        task_id = extract_task_id(
            message
        )

        if task_id is None:

            response = {

                "intent": intent,

                "success": False,

                "message": (
                    "Please provide "
                    "the task ID."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        complete_task(
            task_id
        )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Task {task_id} "
                "completed successfully."
            ),

            "task_id": task_id
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # DELETE TASK
    # =====================================================

    if intent == "delete_task":

        task_id = extract_task_id(
            message
        )

        if task_id is None:

            response = {

                "intent": intent,

                "success": False,

                "message": (
                    "Please provide "
                    "the task ID."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        delete_task(
            task_id
        )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Task {task_id} "
                "deleted successfully."
            ),

            "task_id": task_id
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # CREATE REMINDER
    # =====================================================

    if intent == "create_reminder":

        title = extract_reminder_title(
            message
        )

        reminder_date, reminder_time = (
            extract_reminder_datetime(
                message
            )
        )

        reminder_id = create_reminder(
            title,
            reminder_date,
            reminder_time
        )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Reminder '{title}' "
                "created successfully "
                f"for {reminder_date} "
                f"at {reminder_time}."
            ),

            "reminder_id": reminder_id,

            "reminder_date": reminder_date,

            "reminder_time": reminder_time
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # LIST REMINDERS
    # =====================================================

    if intent == "list_reminders":

        reminders = get_reminders(
            "pending"
        )

        if not reminders:

            response = {

                "intent": intent,

                "success": True,

                "message": (
                    "You currently have "
                    "no pending reminders."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        reminder_list = []

        for reminder in reminders:

            reminder_list.append(
                f"{reminder['id']}. "
                f"{reminder['title']} "
                f"- "
                f"{reminder['reminder_date']} "
                f"at "
                f"{reminder['reminder_time']}"
            )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                "Your upcoming reminders:\n"
                + "\n".join(reminder_list)
            )
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # COMPLETE REMINDER
    # =====================================================

    if intent == "complete_reminder":

        reminder_id = extract_reminder_id(
            message
        )

        if reminder_id is None:

            response = {

                "intent": intent,

                "success": False,

                "message": (
                    "Please provide "
                    "the reminder ID."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        complete_reminder(
            reminder_id
        )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Reminder {reminder_id} "
                "completed successfully."
            ),

            "reminder_id": reminder_id
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # DELETE REMINDER
    # =====================================================

    if intent == "delete_reminder":

        reminder_id = extract_reminder_id(
            message
        )

        if reminder_id is None:

            response = {

                "intent": intent,

                "success": False,

                "message": (
                    "Please provide "
                    "the reminder ID."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        delete_reminder(
            reminder_id
        )

        response = {

            "intent": intent,

            "success": True,

            "message": (
                f"Reminder {reminder_id} "
                "deleted successfully."
            ),

            "reminder_id": reminder_id
        }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # =====================================================
    # GENERAL CHAT
    # =====================================================

    if intent == "general_chat":

        if client is None:

            response = {

                "intent": intent,

                "success": True,

                "message": (
                    "I'm your Intelligent "
                    "AI Productivity Assistant. "
                    "I can help you manage "
                    "tasks, reminders, and "
                    "search your documents."
                )
            }

            save_chat_history(session_id, message, response["message"])

            return response

        response_ai, error_message = (
            generate_gemini_response(
                message
            )
        )

        if response_ai:

            response = {

                "intent": intent,

                "success": True,

                "message": response_ai
            }

        else:

            response = {

                "intent": intent,

                "success": False,

                "message": error_message
            }

        save_chat_history(session_id, message, response["message"])

        return response


    # =====================================================
    # UNKNOWN REQUEST
    # =====================================================

    response = {

        "intent": intent,

        "success": False,

        "message": (
            "I couldn't understand "
            "that request."
        )
    }

    save_chat_history(session_id, message, response["message"])

    return response










