"""Authentication routes for the AI Chatbot Platform."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.database.mongodb import (
    create_user,
    get_user_by_email,
    get_user_by_id,
)
from backend.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.core.security import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


security = HTTPBearer()


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def auth_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "auth",
    }


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=TokenResponse,
)
async def register(
    request: RegisterRequest,
) -> TokenResponse:

    email = request.email.lower().strip()
    full_name = request.full_name.strip()

    # ==========================================
    # CHECK EXISTING USER
    # ==========================================

    existing_user = await get_user_by_email(email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # ==========================================
    # CREATE USER
    # ==========================================

    user_id = str(uuid4())

    password_hash = hash_password(
        request.password,
    )

    user = await create_user(
        user_id=user_id,
        email=email,
        full_name=full_name,
        password_hash=password_hash,
        role="user",
        client_id=request.client_id,
    )

    # ==========================================
    # CREATE JWT
    # ==========================================

    access_token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        client_id=user.get("client_id"),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        client_id=user.get("client_id"),
    )


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
) -> TokenResponse:

    email = request.email.lower().strip()

    # ==========================================
    # FIND USER
    # ==========================================

    user = await get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # ==========================================
    # CHECK ACCOUNT
    # ==========================================

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # ==========================================
    # VERIFY PASSWORD
    # ==========================================

    password_valid = verify_password(
        request.password,
        user["password_hash"],
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # ==========================================
    # CREATE JWT
    # ==========================================

    access_token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        client_id=user.get("client_id"),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        client_id=user.get("client_id"),
    )


# =========================================================
# CURRENT USER
# =========================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> dict:

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

    except JWTError as error:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user = await get_user_by_id(
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


# =========================================================
# ME
# =========================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: dict = Depends(
        get_current_user,
    ),
) -> UserResponse:

    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        client_id=current_user.get("client_id"),
        is_active=current_user.get(
            "is_active",
            True,
        ),
    )