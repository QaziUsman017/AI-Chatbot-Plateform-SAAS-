"""Authentication request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# =========================================================
# REGISTER
# =========================================================

class RegisterRequest(BaseModel):
    """Request body for creating a new user."""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    full_name: str = Field(
        min_length=2,
        max_length=100,
    )
    client_id: str | None = None


# =========================================================
# LOGIN
# =========================================================

class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )


# =========================================================
# TOKEN RESPONSE
# =========================================================

class TokenResponse(BaseModel):
    """JWT authentication response."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: EmailStr
    role: str
    client_id: str | None = None


# =========================================================
# CURRENT USER RESPONSE
# =========================================================

class UserResponse(BaseModel):
    """Public user information."""

    user_id: str
    email: EmailStr
    full_name: str
    role: str
    client_id: str | None = None
    is_active: bool