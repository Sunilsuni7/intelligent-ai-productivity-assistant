from app.database.database import get_connection


def create_task(
    title,
    description="",
    priority="medium",
    due_date=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            title,
            description,
            priority,
            due_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            title,
            description,
            priority,
            due_date
        )
    )

    connection.commit()

    task_id = cursor.lastrowid

    connection.close()

    return task_id


def get_tasks(status=None):
    connection = get_connection()
    cursor = connection.cursor()

    if status:
        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE status = ?
            ORDER BY created_at DESC
            """,
            (status,)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM tasks
            ORDER BY created_at DESC
            """
        )

    tasks = cursor.fetchall()

    connection.close()

    return tasks


def complete_task(task_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET status = 'completed'
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()


def delete_task(task_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()


def update_task_priority(task_id, priority):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET priority = ?
        WHERE id = ?
        """,
        (
            priority,
            task_id
        )
    )

    connection.commit()
    connection.close()


def update_task_due_date(task_id, due_date):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET due_date = ?
        WHERE id = ?
        """,
        (
            due_date,
            task_id
        )
    )

    connection.commit()
    connection.close()
