from datetime import datetime

from app.database.database import get_connection


# =========================================================
# CREATE TASK
# =========================================================

def create_task(title, priority="medium", due_date=None, description=None, session_id="default"):
    """
    Create a new productivity task.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (session_id, title, description, priority, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, title, description, priority, due_date, "pending")
    )

    task_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return task_id


# =========================================================
# GET TASKS
# =========================================================

def get_tasks(session_id="default", status="pending"):
    """
    Return tasks filtered by status.
    """

    connection = get_connection()
    cursor = connection.cursor()

    if status:
        cursor.execute(
            """
            SELECT * FROM tasks WHERE session_id = ? AND status = ?
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END,
                id DESC
            """,
            (session_id, status)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM tasks
            ORDER BY id DESC
            """
        )

    rows = cursor.fetchall()

    tasks = [dict(row) for row in rows]

    connection.close()

    return tasks


# =========================================================
# GET SINGLE TASK
# =========================================================

def get_task(task_id):
    """
    Return one task by ID.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE id = ?
        """,
        (session_id, task_id)
    )

    row = cursor.fetchone()

    connection.close()

    if row:
        return dict(row)

    return None


# =========================================================
# COMPLETE TASK
# =========================================================

def complete_task(task_id, session_id="default"):
    """
    Mark a task as completed.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks SET status = ? WHERE session_id = ? AND id = ?
        """,
        (
            "completed",
            session_id,
            task_id
        )
    )

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated > 0


# =========================================================
# DELETE TASK
# =========================================================

def delete_task(task_id, session_id="default"):
    """
    Delete a task by ID.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM tasks WHERE session_id = ? AND id = ?
        """,
        (session_id, task_id)
    )

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    return deleted > 0


# =========================================================
# UPDATE TASK
# =========================================================

def update_task(
    task_id,
    title=None,
    priority=None,
    due_date=None,
    description=None,
    status=None
):
    """
    Update task fields.
    """

    connection = get_connection()
    cursor = connection.cursor()

    updates = []
    values = []

    if title is not None:
        updates.append("title = ?")
        values.append(title)

    if priority is not None:
        updates.append("priority = ?")
        values.append(priority)

    if due_date is not None:
        updates.append("due_date = ?")
        values.append(due_date)

    if description is not None:
        updates.append("description = ?")
        values.append(description)

    if status is not None:
        updates.append("status = ?")
        values.append(status)

    if not updates:
        connection.close()
        return False

    values.append(task_id)

    query = f"""
        UPDATE tasks
        SET {", ".join(updates)}
        WHERE id = ?
    """

    cursor.execute(
        query,
        values
    )

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated > 0


# =========================================================
# PENDING TASK COUNT
# =========================================================

def get_pending_task_count():
    """
    Return number of pending tasks.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM tasks
        WHERE status = ?
        """,
        ("pending",)
    )

    result = cursor.fetchone()

    connection.close()

    return result["count"] if result else 0


# =========================================================
# TASK EXTRACTION HELPERS
# =========================================================

def extract_task_title(message):
    """
    Extract the task title from a natural-language request.
    """

    text = message.strip()

    patterns = [
        r"^(?:create|add|make)\s+(?:a\s+)?task\s+(?:to\s+)?(.+)$",
        r"^(?:create|add|make)\s+(?:a\s+)?task\s*:\s*(.+)$",
        r"^task\s*:\s*(.+)$",
    ]

    for pattern in patterns:

        match = __import__("re").search(
            pattern,
            text,
            __import__("re").IGNORECASE
        )

        if match:

            title = match.group(1).strip()

            title = __import__("re").sub(
                r"\b(?:high|medium|low)\s+priority\b",
                "",
                title,
                flags=__import__("re").IGNORECASE
            )

            title = __import__("re").sub(
                r"\b(?:today|tomorrow)\b",
                "",
                title,
                flags=__import__("re").IGNORECASE
            )

            return title.strip(" .,:-")

    return text


def extract_task_priority(message):
    """
    Extract task priority.
    """

    text = message.lower()

    if "high priority" in text:
        return "high"

    if "low priority" in text:
        return "low"

    if "medium priority" in text:
        return "medium"

    return "medium"


def extract_task_due_date(message):
    """
    Extract today/tomorrow due date.
    """

    text = message.lower()

    today = datetime.now().date()

    if "tomorrow" in text:

        return (
            today.replace(
                day=today.day
            )
        ).fromordinal(
            today.toordinal() + 1
        ).isoformat()

    if "today" in text:
        return today.isoformat()

    return None


def extract_task_id(message):
    """
    Extract a numeric task ID.
    """

    match = __import__("re").search(
        r"\b(?:task\s*)?#?(\d+)\b",
        message,
        __import__("re").IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None
