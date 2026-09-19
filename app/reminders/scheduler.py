import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.reminders.reminder_manager import get_reminders

INDIA_TZ = ZoneInfo("Asia/Kolkata")

# Keep track of notified reminders to prevent log spam
_notified_reminders = set()

def check_reminders():
    """
    Check pending reminders and log a notification
    when their scheduled date and time are reached.

    The reminder is NOT automatically marked as completed.
    This allows the Streamlit dashboard to continue showing
    the reminder until the user manually completes or deletes it.
    """
    now = datetime.now(INDIA_TZ)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    reminders = get_reminders("pending")

    for reminder in reminders:
        r_id = reminder["id"]
        r_date = reminder["reminder_date"]
        r_time = reminder["reminder_time"]

        if r_date < current_date or (r_date == current_date and r_time <= current_time):
            if r_id not in _notified_reminders:
                # Format properly: 19 Sep 2026 • 10:00 AM IST
                try:
                    dt_obj = datetime.strptime(f"{r_date} {r_time}", "%Y-%m-%d %H:%M")
                    formatted_dt = dt_obj.strftime("%d %b %Y • %I:%M %p") + " IST"
                except Exception:
                    formatted_dt = f"{r_date} • {r_time} IST"

                logging.info(
                    f"\n[REMINDER]\n"
                    f"{reminder['title']}\n"
                    f"Scheduled: {formatted_dt}\n"
                    f"Status: PENDING"
                )
                _notified_reminders.add(r_id)


def start_scheduler():
    """
    Start the background reminder scheduler.
    The scheduler checks reminders every 30 seconds in IST.
    """
    scheduler = BackgroundScheduler(timezone=INDIA_TZ)

    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=30,
        id="reminder_checker",
        replace_existing=True
    )

    scheduler.start()
    logging.info("Reminder scheduler started successfully.")

    return scheduler
