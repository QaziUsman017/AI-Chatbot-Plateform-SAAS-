"""User domain model for authentication and authorization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """Represents a platform user."""

    id: str | None = None
    email: str | None = None
    full_name: str | None = None

    # Password is always stored as a hash.
    password_hash: str | None = None

    # user / admin
    role: str = "user"

    # Client isolation
    client_id: str | None = None

    # Account status
    is_active: bool = True

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None