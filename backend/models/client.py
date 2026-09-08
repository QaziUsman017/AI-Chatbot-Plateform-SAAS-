"""Client domain model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Client:
    """Represents a client tenant or brand."""

    id: str | None = None

    client_id: str | None = None

    name: str | None = None

    business_name: str | None = None

    email: str | None = None

    agent_name: str | None = None

    website: str | None = None

    status: str = "active"

    widget_config: dict = field(
        default_factory=lambda: {
            "primary_color": "#0ea5e9",
            "secondary_color": "#0f172a",
            "text_color": "#0f172a",
            "bot_name": "AI Assistant",
            "logo": "",
            "position": "bottom-right",
            "welcome_message":
                "Hi! How can I help you today?",
        }
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None