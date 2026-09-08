"""Document domain model placeholder."""

from dataclasses import dataclass


@dataclass
class Document:
    """Represents a source document or knowledge asset."""

    id: str | None = None
    client_id: str | None = None
    filename: str | None = None
    filetype: str | None = None
    status: str = "uploaded"
    path: str | None = None
