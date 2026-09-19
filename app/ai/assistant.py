from datetime import datetime, timedelta
import re
import os

from dotenv import load_dotenv
from google import genai

from app.ai.intent import (
    detect_intent,
    extract_task_title,
    extract_task_priority,
    extract_task_due_date,
    extract_reminder_title,
    extract_task_id,
    extract_reminder_id
)

from app.tasks.task_manager import (
    create_task,
    get_tasks,
    complete_task,
    delete_task
)

from app.reminders.reminder_manager import (
    create_reminder,
    get_reminders,
    complete_reminder,
    delete_reminder
)

from app.documents.document_manager import search_documents

from app.database.database import get_connection


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = None

if api_key:
    client = genai.Client(
        api_key=api_key
    )

GEMINI_MODEL = "gemini-3.6-flash"


# =========================================================
# CONSTANTS
# =========================================================

DOCUMENT_NOT_FOUND_MESSAGE = (
    "I couldn't find that information in the available documents."
)


# =========================================================
# TEXT RELEVANCE CHECK
# =========================================================

def check_document_relevance(question, document_content):
    """
    Perform a lightweight local relevance check before
    sending the document to Gemini.
    """

    if not question or not document_content:
        return False

    question_words = set(
        re.findall(
            r"\b[a-zA-Z]{3,}\b",
            question.lower()
        )
    )

    document_words = set(
        re.findall(
            r"\b[a-zA-Z]{3,}\b",
            document_content.lower()
        )
    )

    if not question_words or not document_words:
        return False

    stop_words = {
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "have",
        "has",
        "had",
        "this",
        "that",
        "these",
        "those",
        "with",
        "from",
        "about",
        "into",
        "under",
        "according",
        "company",
        "policy",
        "information",
        "tell",
        "please",
        "there",
        "their",
        "they",
        "are",
        "the",
        "and",
        "for",
        "you",
        "your"
    }

    question_keywords = (
        question_words - stop_words
    )

    document_keywords = (
        document_words - stop_words
    )

    if not question_keywords:
        return True

    matching_words = (
        question_keywords
        & document_keywords
    )

    return bool(matching_words)


# =========================================================
# GEMINI AI HELPER
# =========================================================

def generate_gemini_response(prompt):
    """
    Generate a response using Gemini Interactions API.
    """

    if client is None:
        return (
            None,
            "Gemini API key is not configured. "
            "Please check your .env file."
        )

    import threading
    import queue
    q = queue.Queue()

    def worker():
        try:
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt
            )
            q.put((interaction, None))
        except Exception as error:
            q.put((None, error))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    try:
        interaction, error = q.get(timeout=2.0)
        if error:
            return None, f"Gemini error: {error}"
        if interaction and interaction.output_text:
            return interaction.output_text.strip(), None
        return None, "Gemini returned an empty response."
    except queue.Empty:
        return None, "Gemini error: Rate limit exceeded (HTTP 429)."


# =========================================================
# CHAT HISTORY
# =========================================================

import re

def save_chat_history(
    user_message,
    assistant_response
):

    # Redact sensitive API keys or environment variables
    redact_pattern = r"(?i)(api[_-]?key|secret|token|password)([\s:=]+)[^\s]+"
    user_message = re.sub(redact_pattern, r"\1\2[REDACTED]", user_message)
    assistant_response = re.sub(redact_pattern, r"\1\2[REDACTED]", assistant_response)

    # Redact specific known key formats if they appear standalone
    key_pattern = r"(AIza[a-zA-Z0-9_-]{35}|sk-[a-zA-Z0-9]{32,})"
    user_message = re.sub(key_pattern, "[REDACTED]", user_message)
    assistant_response = re.sub(key_pattern, "[REDACTED]", assistant_response)

    connection = get_connection()
    cursor = connection.cursor()

    # Do not duplicate the exact same consecutive conversation record
    cursor.execute(
        "SELECT user_message, assistant_response FROM chat_history ORDER BY id DESC LIMIT 1"
    )
    last_record = cursor.fetchone()
    if last_record:
        if last_record["user_message"] == user_message and last_record["assistant_response"] == assistant_response:
            connection.close()
            return

    cursor.execute(
        """
        INSERT INTO chat_history (
            user_message,
            assistant_response
        )
        VALUES (?, ?)
        """,
        (
            user_message,
            assistant_response
        )
    )

    connection.commit()
    connection.close()


def get_chat_history(limit=50):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_history
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,)
    )

    history = cursor.fetchall()

    connection.close()

    return history


# =========================================================
# DOCUMENT AI ANSWER
# =========================================================

def generate_ai_answer(
    question,
    document_content
):
    """
    Generate an AI answer using ONLY the retrieved
    document content.
    """

    if client is None:

        return (
            "Gemini API key is not configured. "
            "Please check your .env file."
        )

    is_relevant = check_document_relevance(
        question,
        document_content
    )

    if not is_relevant:

        print(
            "Document relevance check failed. "
            "Gemini request skipped."
        )

        return DOCUMENT_NOT_FOUND_MESSAGE

    prompt = f"""
You are an intelligent enterprise productivity assistant.

Answer the user's question using ONLY the information
contained in the retrieved document.

Important rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not present in the document,
   say exactly:
   "I couldn't find that information in the available documents."
4. Keep the answer short and professional.
5. Clearly explain the relevant policy or information.
6. If the document contains related information but
   does not answer the exact question, use the exact
   sentence from rule 3.

User question:
{question}

Retrieved document:
{document_content}
"""

    import threading
    import queue

    q = queue.Queue()

    def worker():
        res, err = generate_gemini_response(prompt)
        q.put((res, err))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    try:
        ai_response, error_message = q.get(timeout=3.0)
        if ai_response:
            return ai_response
    except queue.Empty:
        error_message = "Gemini request timed out."

    return (
        f"Gemini is unavailable ({error_message}). "
        f"Here is the relevant information from the document:\n\n"
        f"{document_content.strip()}"
    )


# =========================================================
# REMINDER DATE AND TIME EXTRACTION
# =========================================================

def extract_reminder_datetime(message):

    now = datetime.now()

    text = message.lower().strip()

    if "tomorrow" in text:

        reminder_date = (
            now.date()
            + timedelta(days=1)
        )

    elif "today" in text:

        reminder_date = now.date()

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

def process_message(message):

    intent = detect_intent(message)


    # =====================================================
    # CREATE TASK
    # =====================================================

    if intent == "create_task":

        title = extract_task_title(
            message
        )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

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

            save_chat_history(
                message,
                response["message"]
            )

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

        save_chat_history(
            message,
            response["message"]
        )

        return response


    # =====================================================
    # DOCUMENT SEARCH
    # =====================================================

    if intent == "document_search":

        results = search_documents(
            message
        )

        if not results:

            response = {

                "intent": intent,

                "success": True,

                "message": (
                    DOCUMENT_NOT_FOUND_MESSAGE
                )
            }

            save_chat_history(
                message,
                response["message"]
            )

            return response

        best_result = results[0]

        document_content = (
            best_result["content"]
        )

        if not check_document_relevance(
            message,
            document_content
        ):

            response = {

                "intent": intent,

                "success": True,

                "message": (
                    DOCUMENT_NOT_FOUND_MESSAGE
                ),

                "source": (
                    best_result["filename"]
                ),

                "relevance_score": (
                    best_result["score"]
                )
            }

            save_chat_history(
                message,
                response["message"]
            )

            return response

        ai_answer = generate_ai_answer(
            message,
            document_content
        )

        response = {

            "intent": intent,

            "success": True,

            "message": ai_answer,

            "source": (
                best_result["filename"]
            ),

            "relevance_score": (
                best_result["score"]
            )
        }

        save_chat_history(
            message,
            response["message"]
        )

        return response


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

            save_chat_history(message, response["message"])
            return response

        response_ai, error_message = generate_gemini_response(message)

        if response_ai:
            response = {
                "intent": intent,
                "success": True,
                "message": response_ai
            }
        else:
            # Fallback handling for API exhaustion
            if "Rate limit exceeded" in error_message or "429" in error_message or "too_many_requests" in error_message:
                error_message = (
                    "Gemini Free Tier limit has been reached. "
                    "Your productivity data and document search are still available, "
                    "but AI-generated responses are temporarily unavailable."
                )

            response = {
                "intent": intent,
                "success": False,
                "message": error_message
            }

        save_chat_history(message, response["message"])
        return response


    # =====================================================
    # UNKNOWN REQUEST
    # =====================================================

    response = {
        "intent": intent,
        "success": False,
        "message": "I couldn't understand that request."
    }

    save_chat_history(message, response["message"])
    return response
