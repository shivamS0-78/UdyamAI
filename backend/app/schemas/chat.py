from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)
    language: str = Field(default="en", pattern=r"^(en|hi|mr)$")


class ChatResponse(BaseModel):
    reply: str
    provider_available: bool = True
