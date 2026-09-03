from fastapi import APIRouter

from app.ai.chat import generate_chat_reply
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
def post_chat(req: ChatRequest):
    reply, available = generate_chat_reply(
        message=req.message,
        history=req.history,
        language=req.language,
    )
    return ChatResponse(reply=reply, provider_available=available)
