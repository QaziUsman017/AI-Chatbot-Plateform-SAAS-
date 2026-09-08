"""Client-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    """Schema for creating a client."""

    name: str = Field(..., min_length=2)
    email: EmailStr


class ClientRead(BaseModel):
    """Schema for reading a client."""

    id: str | None = None
    name: str | None = None
    email: str | None = None
    status: str = "active"
