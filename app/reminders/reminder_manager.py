import re

from app.database.database import get_connection


# =========================================================
# CREATE REMINDER
# =========================================================

def create_reminder(session_id, 
    title,
    reminder_date,
    reminder_time
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reminders (
            session_id,
            title,
            reminder_date,
            reminder_time,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            title,
            reminder_date,
            reminder_time,
            "pending"
        )
    )

    connection.commit()

    reminder_id = cursor.lastrowid

    connection.close()

    return reminder_id


# =========================================================
# GET REMINDERS
# =========================================================

def get_reminders(session_id="default", status=None):

    connection = get_connection()
    cursor = connection.cursor()

    if status:

        cursor.execute(
            """
            SELECT *
            FROM reminders
            WHERE session_id = ? AND status = ?
            ORDER BY reminder_date, reminder_time
            """,
            (session_id, status)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM reminders
            WHERE session_id = ?
            ORDER BY reminder_date, reminder_time
            """,
            (session_id,)
        )

    reminders = cursor.fetchall()

    connection.close()

    return reminders


# =========================================================
# GET SINGLE REMINDER
# =========================================================

def get_reminder(reminder_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reminders
        WHERE id = ?
        """,
        (session_id, reminder_id)
    )

    reminder = cursor.fetchone()

    connection.close()

    return reminder


# =========================================================
# COMPLETE REMINDER
# =========================================================

def complete_reminder(reminder_id, session_id="default"):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reminders SET status = 'completed' WHERE session_id = ? AND id = ?
        """,
        (session_id, reminder_id)
    )

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated > 0


# =========================================================
# DELETE REMINDER
# =========================================================

def delete_reminder(reminder_id, session_id="default"):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM reminders WHERE session_id = ? AND id = ?
        """,
        (session_id, reminder_id)
    )

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    return deleted > 0


# =========================================================
# EXTRACT REMINDER TITLE
# =========================================================

def extract_reminder_title(message):
    """
    Extract the reminder title from a user message.

    Examples:
        remind me to finish my project
        create reminder to submit resume tomorrow
        remind me to study at 6 PM
    """

    text = message.strip()

    patterns = [
        r"^remind\s+me\s+to\s+(.+)$",
        r"^reminder\s*:\s*(.+)$",
        r"^create\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
        r"^add\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
        r"^make\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
    ]

    title = text

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()
            break

    # Remove date/time information from the title.

    title = re.sub(
        r"\b(today|tomorrow)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b(?:at|on)\s+"
        r"(?:[01]?\d|2[0-3])"
        r"(?::[0-5]\d)?"
        r"\s*(?:am|pm)?\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b(?:at|on)\s+"
        r"(?:1[0-2]|0?[1-9])"
        r"(?:\s*:\s*[0-5]\d)?"
        r"\s*(?:am|pm)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip(" .,:-")


# =========================================================
# EXTRACT REMINDER ID
# =========================================================

def extract_reminder_id(message):
    """
    Extract numeric reminder ID.

    Examples:
        complete reminder 5
        delete reminder #5
        reminder 5
    """

    match = re.search(
        r"\b(?:reminder\s*)?#?(\d+)\b",
        message,
        re.IGNORECASE
    )

    if match:

        return int(
            match.group(1)
        )

    return None