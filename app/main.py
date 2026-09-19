from fastapi import FastAPI

from app.api.routes import router
from app.reminders.scheduler import start_scheduler


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Intelligent AI Productivity Assistant",
    description="AI-powered productivity assistant API",
    version="1.0.0"
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# START REMINDER SCHEDULER
# ============================================================

scheduler = start_scheduler()