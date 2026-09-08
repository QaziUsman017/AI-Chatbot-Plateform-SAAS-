"""Conversation domain model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Conversation:
    """Represents a user conversation thread."""

    id: str | None = None

    conversation_id: str | None = None

    client_id: str | None = None

    chatbot_id: str | None = None

    user_id: str | None = None

    title: str | None = None

    messages: list[dict] = field(
        default_factory=list
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None