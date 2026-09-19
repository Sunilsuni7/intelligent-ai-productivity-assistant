from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.assistant import process_message


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    source: str = "text"
    session_id: str = "default"


@router.get("/")
def home():
    return {
        "message": "Intelligent AI Productivity Assistant API is running!"
    }

@router.get("/health")
def health_check():
    import os
    try:
        from app.database.database import get_connection
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


from app.agent.agent import handle_request
from app.agent.models import AgentRequest

@router.post("/chat")
def chat(request: ChatRequest):
    agent_req = AgentRequest(message=request.message, source=request.source, session_id=request.session_id)
    result = handle_request(agent_req)
    # The existing frontend expects {"success": True, "message": "..."}
    return result
