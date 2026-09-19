from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.reminders.reminder_manager import get_reminders


def check_reminders():
    """
    Check pending reminders and print a notification
    when their scheduled date and time are reached.

    The reminder is NOT automatically marked as completed.
    This allows the Streamlit dashboard to continue showing
    the reminder until the user manually completes or deletes it.
    """

    now = datetime.now()

    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    reminders = get_reminders("pending")

    for reminder in reminders:

        reminder_date = reminder["reminder_date"]
        reminder_time = reminder["reminder_time"]

        if (
            reminder_date == current_date
            and reminder_time <= current_time
        ):

            print(
                "\n"
                "========================================\n"
                "🔔 REMINDER\n"
                "========================================\n"
                f"{reminder['title']}\n"
                f"Scheduled: {reminder_date} "
                f"at {reminder_time}\n"
                "Status: PENDING\n"
                "========================================\n"
            )


def start_scheduler():
    """
    Start the background reminder scheduler.

    The scheduler checks reminders every 30 seconds.
    """

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=30,
        id="reminder_checker",
        replace_existing=True
    )

    scheduler.start()

    print(
        "⏰ Reminder scheduler started successfully."
    )

    return scheduler

