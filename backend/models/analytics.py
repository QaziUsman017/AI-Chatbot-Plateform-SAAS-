"""Analytics domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""

    id: str | None = None

    client_id: str | None = None

    visitor_id: str | None = None

    chatbot_id: str | None = None

    conversation_id: str | None = None

    event_type: str = "view"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass
class Visitor:
    """Represents a unique website visitor."""

    visitor_id: str

    client_id: str

    first_seen_at: datetime | None = None

    last_seen_at: datetime | None = None

    visit_count: int = 1


@dataclass
class AnalyticsSummary:
    """Aggregated analytics for a client or platform."""

    visitors: int = 0

    conversations: int = 0

    messages: int = 0

    response_time_ms: float | None = None

    resolution_rate: float | None = None

    active_clients: int = 0

    documents: int = 0