"""Message domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Represents one message in a conversation."""

    id: str | None = None

    conversation_id: str | None = None

    client_id: str | None = None

    role: str = "user"

    content: str = ""

    metadata: dict | None = None

    created_at: datetime | None = None