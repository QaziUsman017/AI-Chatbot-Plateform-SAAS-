"""Chat-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a chat request."""

    role: str = Field(default="user")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Request payload for a chat completion."""

    chatbot_id: str | None = None
    conversation_id: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response payload for a chat completion."""

    response: str
    conversation_id: str | None = None
