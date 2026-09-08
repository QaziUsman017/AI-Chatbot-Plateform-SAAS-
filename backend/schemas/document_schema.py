"""Document-related Pydantic schemas."""

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """Metadata for an uploaded document."""

    filename: str = Field(..., min_length=1)
    filetype: str = Field(default="application/octet-stream")
    client_id: str | None = None


class DocumentRead(BaseModel):
    """Metadata for a stored document."""

    id: str | None = None
    filename: str | None = None
    filetype: str | None = None
    status: str = "uploaded"
