"""Chatbot-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ChatbotCreate(BaseModel):
    """Schema for creating a chatbot configuration."""

    name: str = Field(..., min_length=2)
    model_name: str = Field(default="gpt-4o-mini")
    status: str = Field(default="draft")


class ChatbotRead(BaseModel):
    """Schema for reading a chatbot configuration."""

    id: str | None = None
    name: str | None = None
    model_name: str | None = None
    status: str = "draft"
