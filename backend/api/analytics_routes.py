"""Analytics API routes."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from backend.api.auth_routes import (
    get_current_user,
)

from backend.services.analytics.analytics_service import (
    get_analytics,
)


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def analytics_health() -> dict[str, str]:

    return {
        "status": "ok",
        "module": "analytics",
    }


# =========================================================
# ANALYTICS
# =========================================================

@router.get("")
async def analytics(
    client_id: str | None = None,
    current_user: dict = Depends(
        get_current_user
    ),
) -> dict:

    role = str(
        current_user.get(
            "role",
            "user",
        )
    ).lower()

    authenticated_client_id = (
        current_user.get(
            "client_id"
        )
    )

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if role == "admin":

        selected_client_id = (
            client_id.strip()
            if client_id
            else None
        )

    # -----------------------------------------------------
    # NORMAL USER
    # -----------------------------------------------------

    else:

        if not authenticated_client_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "User is not associated "
                    "with a client."
                ),
            )

        authenticated_client_id = (
            authenticated_client_id.strip()
        )

        if (
            client_id
            and client_id.strip()
            != authenticated_client_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You are not authorized "
                    "to access this client's analytics."
                ),
            )

        selected_client_id = (
            authenticated_client_id
        )

    # -----------------------------------------------------
    # GET ANALYTICS
    # -----------------------------------------------------

    data = await get_analytics(
        client_id=selected_client_id
    )

    return {
        "analytics": data
    }