id="m7q2vx"
from app.database.database import get_connection


# =========================================================
# CREATE REMINDER
# =========================================================

def create_reminder(
    title,
    reminder_date,
    reminder_time
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reminders (
            title,
            reminder_date,
            reminder_time
        )
        VALUES (?, ?, ?)
        """,
        (
            title,
            reminder_date,
            reminder_time
        )
    )

    connection.commit()

    reminder_id = cursor.lastrowid

    connection.close()

    return reminder_id


# =========================================================
# GET REMINDERS
# =========================================================

def get_reminders(status=None):

    connection = get_connection()
    cursor = connection.cursor()

    if status:

        cursor.execute(
            """
            SELECT *
            FROM reminders
            WHERE status = ?
            ORDER BY reminder_date, reminder_time
            """,
            (status,)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM reminders
            ORDER BY reminder_date, reminder_time
            """
        )

    reminders = cursor.fetchall()

    connection.close()

    return reminders


# =========================================================
# COMPLETE REMINDER
# =========================================================

def complete_reminder(reminder_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reminders
        SET status = 'completed'
        WHERE id = ?
        """,
        (reminder_id,)
    )

    connection.commit()

    connection.close()


# =========================================================
# DELETE REMINDER
# =========================================================

def delete_reminder(reminder_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM reminders
        WHERE id = ?
        """,
        (reminder_id,)
    )

    connection.commit()

    connection.close()
