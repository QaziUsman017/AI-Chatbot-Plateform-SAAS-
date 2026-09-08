"""Chatbot domain model placeholder."""

from dataclasses import dataclass


@dataclass
class Chatbot:
    """Represents an AI chatbot instance."""

    id: str | None = None
    client_id: str | None = None
    name: str | None = None
    status: str = "draft"
    model_name: str | None = None
