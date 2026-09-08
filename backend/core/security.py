"""Security utilities for authentication and JWT tokens."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from jose import jwt


load_dotenv()


# =========================================================
# JWT CONFIGURATION
# =========================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured in the .env file."
    )


JWT_ALGORITHM = "HS256"


JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(
    password: str,
) -> str:
    """Hash a password using bcrypt."""

    password_bytes = password.encode(
        "utf-8"
    )

    if len(password_bytes) > 72:
        raise ValueError(
            "Password cannot be longer than 72 bytes."
        )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return hashed.decode(
        "utf-8"
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verify a password."""

    password_bytes = password.encode(
        "utf-8"
    )

    if len(password_bytes) > 72:
        return False

    return bcrypt.checkpw(
        password_bytes,
        password_hash.encode(
            "utf-8"
        ),
    )


# =========================================================
# JWT
# =========================================================

def create_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    client_id: str | None = None,
) -> str:
    """Create a JWT access token."""

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "client_id": client_id,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict:
    """Decode and validate a JWT access token."""

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[
            JWT_ALGORITHM
        ],
    )