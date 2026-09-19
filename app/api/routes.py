from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.assistant import process_message


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/")
def home():
    return {
        "message": "Intelligent AI Productivity Assistant API is running!"
    }


@router.post("/chat")
def chat(request: ChatRequest):
    result = process_message(request.message)

    return result