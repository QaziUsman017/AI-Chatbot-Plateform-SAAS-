"""
Routes for client and AI agent management.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel, Field

from backend.database.mongodb import (
    create_client,
    get_client,
    clients_collection,
    get_widget_config,
    update_widget_config,
    delete_client_data,
)

from backend.core.security import decode_access_token


router = APIRouter(
    prefix="/clients",
    tags=["clients"],
)

security = HTTPBearer()


# =========================================================
# DEFAULT WIDGET CONFIG
# =========================================================

DEFAULT_WIDGET_CONFIG = {
    "primary_color": "#0ea5e9",
    "secondary_color": "#0f172a",
    "text_color": "#0f172a",

    "bot_name": "AI Assistant",
    "logo": "",
    "position": "bottom-right",
    "welcome_message": "Hi! How can I help you today?",

    # Widget backgrounds
    "background_color": "#0b0d0c",
    "surface_color": "#111513",
    "surface_secondary_color": "#161a18",
    "surface_tertiary_color": "#1c211f",

    # Text colors
    "text_primary_color": "#f5f7f6",
    "text_secondary_color": "#d8dedb",
    "text_muted_color": "#929b97",
    "text_muted_dark_color": "#68716d",

    # Borders
    "border_color": "rgba(255,255,255,0.08)",
    "border_light_color": "rgba(255,255,255,0.12)",

    # Header
    "header_background_color": "#111513",
    "header_text_color": "#f5f7f6",
    "header_secondary_text_color": "#929b97",
    "header_button_color": "#929b97",
    "header_button_background_color": "rgba(255,255,255,0.06)",
    "header_button_border_color": "rgba(255,255,255,0.08)",

    # Avatar / welcome icon
    "avatar_background_color": "#10b981",
    "avatar_text_color": "#ffffff",
    "welcome_icon_background_color": "#10b981",
    "welcome_icon_text_color": "#ffffff",

    # Status
    "status_dot_color": "#22c55e",
    "status_text_color": "#929b97",

    # User message
    "user_message_background_color": "#242a27",
    "user_message_text_color": "#f2f5f3",
    "user_message_border_color": "rgba(255,255,255,0.09)",

    # Assistant message
    "assistant_message_background_color": "#1b211f",
    "assistant_message_text_color": "#e7ece9",
    "assistant_message_border_color": "rgba(255,255,255,0.10)",

    # Composer / input
    "composer_background_color": "#111513",
    "input_background_color": "#161a18",
    "input_text_color": "#f5f7f6",
    "input_placeholder_color": "#929b97",
    "input_border_color": "rgba(255,255,255,0.10)",
    "input_focus_border_color": "#10b981",

    # Send / launcher
    "send_button_background_color": "#10b981",
    "send_button_text_color": "#ffffff",
    "launcher_background_color": "#10b981",
    "launcher_icon_color": "#ffffff",

    # Other
    "typing_background_color": "#161a18",
    "typing_dot_color": "#929b97",
    "code_background_color": "#0b0e0d",
    "code_text_color": "#e7ece9",
    "danger_color": "#ef4444",
    "success_color": "#22c55e",
}


ALLOWED_POSITIONS = {
    "bottom-right",
    "bottom-left",
    "top-right",
    "top-left",
}


# =========================================================
# REQUEST MODELS
# =========================================================

class ClientCreateRequest(BaseModel):
    client_id: str
    business_name: str
    agent_name: str
    website: str = ""


class ClientUpdateRequest(BaseModel):
    business_name: str | None = None
    agent_name: str | None = None
    website: str | None = None


class WidgetConfigRequest(BaseModel):

    primary_color: str = Field(
        default="#0ea5e9",
        min_length=1,
        max_length=100,
    )

    secondary_color: str = Field(
        default="#0f172a",
        min_length=1,
        max_length=100,
    )

    text_color: str = Field(
        default="#0f172a",
        min_length=1,
        max_length=100,
    )

    bot_name: str = Field(
        default="AI Assistant",
        min_length=1,
        max_length=100,
    )

    logo: str = Field(
        default="",
        max_length=2_000_000,
    )

    position: str = Field(
        default="bottom-right",
        min_length=1,
        max_length=30,
    )

    welcome_message: str = Field(
        default="Hi! How can I help you today?",
        min_length=1,
        max_length=500,
    )

    background_color: str = Field(
        default="#0b0d0c",
        max_length=100,
    )

    surface_color: str = Field(
        default="#111513",
        max_length=100,
    )

    surface_secondary_color: str = Field(
        default="#161a18",
        max_length=100,
    )

    surface_tertiary_color: str = Field(
        default="#1c211f",
        max_length=100,
    )

    text_primary_color: str = Field(
        default="#f5f7f6",
        max_length=100,
    )

    text_secondary_color: str = Field(
        default="#d8dedb",
        max_length=100,
    )

    text_muted_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    text_muted_dark_color: str = Field(
        default="#68716d",
        max_length=100,
    )

    border_color: str = Field(
        default="rgba(255,255,255,0.08)",
        max_length=100,
    )

    border_light_color: str = Field(
        default="rgba(255,255,255,0.12)",
        max_length=100,
    )

    header_background_color: str = Field(
        default="#111513",
        max_length=100,
    )

    header_text_color: str = Field(
        default="#f5f7f6",
        max_length=100,
    )

    header_secondary_text_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    header_button_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    header_button_background_color: str = Field(
        default="rgba(255,255,255,0.06)",
        max_length=100,
    )

    header_button_border_color: str = Field(
        default="rgba(255,255,255,0.08)",
        max_length=100,
    )

    avatar_background_color: str = Field(
        default="#10b981",
        max_length=100,
    )

    avatar_text_color: str = Field(
        default="#ffffff",
        max_length=100,
    )

    welcome_icon_background_color: str = Field(
        default="#10b981",
        max_length=100,
    )

    welcome_icon_text_color: str = Field(
        default="#ffffff",
        max_length=100,
    )

    status_dot_color: str = Field(
        default="#22c55e",
        max_length=100,
    )

    status_text_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    user_message_background_color: str = Field(
        default="#242a27",
        max_length=100,
    )

    user_message_text_color: str = Field(
        default="#f2f5f3",
        max_length=100,
    )

    user_message_border_color: str = Field(
        default="rgba(255,255,255,0.09)",
        max_length=100,
    )

    assistant_message_background_color: str = Field(
        default="#1b211f",
        max_length=100,
    )

    assistant_message_text_color: str = Field(
        default="#e7ece9",
        max_length=100,
    )

    assistant_message_border_color: str = Field(
        default="rgba(255,255,255,0.10)",
        max_length=100,
    )

    composer_background_color: str = Field(
        default="#111513",
        max_length=100,
    )

    input_background_color: str = Field(
        default="#161a18",
        max_length=100,
    )

    input_text_color: str = Field(
        default="#f5f7f6",
        max_length=100,
    )

    input_placeholder_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    input_border_color: str = Field(
        default="rgba(255,255,255,0.10)",
        max_length=100,
    )

    input_focus_border_color: str = Field(
        default="#10b981",
        max_length=100,
    )

    send_button_background_color: str = Field(
        default="#10b981",
        max_length=100,
    )

    send_button_text_color: str = Field(
        default="#ffffff",
        max_length=100,
    )

    launcher_background_color: str = Field(
        default="#10b981",
        max_length=100,
    )

    launcher_icon_color: str = Field(
        default="#ffffff",
        max_length=100,
    )

    typing_background_color: str = Field(
        default="#161a18",
        max_length=100,
    )

    typing_dot_color: str = Field(
        default="#929b97",
        max_length=100,
    )

    code_background_color: str = Field(
        default="#0b0e0d",
        max_length=100,
    )

    code_text_color: str = Field(
        default="#e7ece9",
        max_length=100,
    )

    danger_color: str = Field(
        default="#ef4444",
        max_length=100,
    )

    success_color: str = Field(
        default="#22c55e",
        max_length=100,
    )


# =========================================================
# AUTHENTICATION
# =========================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token.",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    return payload


# =========================================================
# HELPERS
# =========================================================

def validate_color(value: str) -> bool:

    value = str(value or "").strip()

    if not value:
        return False

    if value.startswith("#"):

        hex_part = value[1:]

        if len(hex_part) in {3, 4, 6, 8}:

            return all(
                char in "0123456789abcdefABCDEF"
                for char in hex_part
            )

        return False

    allowed_prefixes = (
        "rgb(",
        "rgba(",
        "hsl(",
        "hsla(",
        "oklch(",
        "oklab(",
        "color(",
    )

    lower_value = value.lower()

    if lower_value.startswith(
        allowed_prefixes
    ):
        return True

    return lower_value in {
        "black",
        "white",
        "red",
        "blue",
        "green",
        "transparent",
        "yellow",
        "orange",
        "purple",
        "pink",
        "gray",
        "grey",
    }


def normalize_widget_config(
    request: WidgetConfigRequest,
) -> dict:

    data = request.model_dump()

    for key, value in data.items():

        if isinstance(value, str):
            data[key] = value.strip()

    color_fields = [

        "primary_color",
        "secondary_color",
        "text_color",

        "background_color",
        "surface_color",
        "surface_secondary_color",
        "surface_tertiary_color",

        "text_primary_color",
        "text_secondary_color",
        "text_muted_color",
        "text_muted_dark_color",

        "border_color",
        "border_light_color",

        "header_background_color",
        "header_text_color",
        "header_secondary_text_color",
        "header_button_color",
        "header_button_background_color",
        "header_button_border_color",

        "avatar_background_color",
        "avatar_text_color",

        "welcome_icon_background_color",
        "welcome_icon_text_color",

        "status_dot_color",
        "status_text_color",

        "user_message_background_color",
        "user_message_text_color",
        "user_message_border_color",

        "assistant_message_background_color",
        "assistant_message_text_color",
        "assistant_message_border_color",

        "composer_background_color",
        "input_background_color",
        "input_text_color",
        "input_placeholder_color",
        "input_border_color",
        "input_focus_border_color",

        "send_button_background_color",
        "send_button_text_color",

        "launcher_background_color",
        "launcher_icon_color",

        "typing_background_color",
        "typing_dot_color",

        "code_background_color",
        "code_text_color",

        "danger_color",
        "success_color",
    ]

    for field_name in color_fields:

        value = data.get(field_name)

        if not validate_color(value):

            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}.",
            )

    if not data["bot_name"]:

        raise HTTPException(
            status_code=400,
            detail="bot_name cannot be empty.",
        )

    if not data["welcome_message"]:

        raise HTTPException(
            status_code=400,
            detail="welcome_message cannot be empty.",
        )

    data["position"] = data["position"].lower()

    if data["position"] not in ALLOWED_POSITIONS:

        raise HTTPException(
            status_code=400,
            detail="Invalid widget position.",
        )

    if len(data["logo"]) > 2_000_000:

        raise HTTPException(
            status_code=400,
            detail="Logo is too large.",
        )

    return {
        key: data[key]
        for key in DEFAULT_WIDGET_CONFIG.keys()
    }


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def client_health() -> dict[str, str]:

    return {
        "status": "ok",
        "module": "clients",
    }


# =========================================================
# CURRENT USER CLIENT
# =========================================================

@router.get("/me")
async def get_my_client(
    current_user: dict = Depends(get_current_user),
) -> dict:

    client_id = current_user.get("client_id")

    if not client_id:

        raise HTTPException(
            status_code=404,
            detail="No client is assigned to this user.",
        )

    client = await get_client(client_id)

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    client.pop("_id", None)

    return client


# =========================================================
# LIST CLIENTS
# =========================================================

@router.get("")
async def get_clients(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:

    role = current_user.get("role")
    client_id = current_user.get("client_id")

    if role == "admin":

        cursor = clients_collection.find(
            {},
            {
                "_id": 0,
            },
        ).sort(
            "created_at",
            -1,
        )

        return await cursor.to_list(
            length=100
        )

    if not client_id:
        return []

    client = await get_client(
        client_id
    )

    if not client:
        return []

    client.pop("_id", None)

    return [client]


# =========================================================
# CREATE CLIENT
# =========================================================

@router.post("")
async def create_new_client(
    request: ClientCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:

    if current_user.get("role") != "admin":

        raise HTTPException(
            status_code=403,
            detail="Only administrators can create clients.",
        )

    client_id = request.client_id.strip()
    business_name = request.business_name.strip()
    agent_name = request.agent_name.strip()
    website = request.website.strip()

    if not client_id:

        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    if not business_name:

        raise HTTPException(
            status_code=400,
            detail="business_name cannot be empty.",
        )

    if not agent_name:

        raise HTTPException(
            status_code=400,
            detail="agent_name cannot be empty.",
        )

    existing_client = await get_client(
        client_id
    )

    if existing_client:

        raise HTTPException(
            status_code=409,
            detail="A client with this client_id already exists.",
        )

    await create_client(
        client_id=client_id,
        business_name=business_name,
        agent_name=agent_name,
        website=website,
    )

    return {
        "message": "Client created successfully.",
        "client_id": client_id,
        "business_name": business_name,
        "agent_name": agent_name,
    }


# =========================================================
# DELETE CLIENT
# =========================================================

@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:

    # -----------------------------------------------------
    # ADMIN ONLY
    # -----------------------------------------------------

    if current_user.get("role") != "admin":

        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete clients.",
        )

    requested_client_id = client_id.strip()

    if not requested_client_id:

        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    # -----------------------------------------------------
    # Verify client exists
    # -----------------------------------------------------

    client = await get_client(
        requested_client_id
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    business_name = (
        client.get("business_name")
        or requested_client_id
    )

    # -----------------------------------------------------
    # Cascade delete
    # -----------------------------------------------------

    deletion_result = await delete_client_data(
        requested_client_id
    )

    if not deletion_result.get(
        "client_deleted"
    ):

        raise HTTPException(
            status_code=404,
            detail="Client could not be deleted.",
        )

    return {
        "message": "Client deleted successfully.",
        "client_id": requested_client_id,
        "business_name": business_name,
        "deleted": {
            "agents": deletion_result.get(
                "agents_deleted",
                0,
            ),
            "agent_configs": deletion_result.get(
                "agent_configs_deleted",
                0,
            ),
            "conversations": deletion_result.get(
                "conversations_deleted",
                0,
            ),
            "visitors": deletion_result.get(
                "visitors_deleted",
                0,
            ),
            "analytics_events": deletion_result.get(
                "analytics_events_deleted",
                0,
            ),
            "documents": deletion_result.get(
                "documents_deleted",
                0,
            ),
            "users_unassigned": deletion_result.get(
                "users_unassigned",
                0,
            ),
        },
    }


# =========================================================
# GET CLIENT BY ID
# =========================================================

@router.get("/{client_id}")
async def get_client_details(
    client_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:

    requested_client_id = client_id.strip()

    if current_user.get("role") != "admin":

        own_client_id = current_user.get(
            "client_id"
        )

        if requested_client_id != own_client_id:

            raise HTTPException(
                status_code=403,
                detail="You do not have access to this client.",
            )

    client = await get_client(
        requested_client_id
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    client.pop("_id", None)

    return client


# =========================================================
# GET WIDGET CONFIG
# =========================================================

@router.get("/{client_id}/widget-config")
async def get_client_widget_config(
    client_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:

    requested_client_id = client_id.strip()

    if current_user.get("role") != "admin":

        own_client_id = current_user.get(
            "client_id"
        )

        if requested_client_id != own_client_id:

            raise HTTPException(
                status_code=403,
                detail="You do not have access to this client.",
            )

    client = await get_client(
        requested_client_id
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    stored_config = await get_widget_config(
        requested_client_id
    )

    config = {
        **DEFAULT_WIDGET_CONFIG,
        **(stored_config or {}),
    }

    config.pop("_id", None)

    return {
        "client_id": requested_client_id,
        "config": config,
    }


# =========================================================
# SAVE WIDGET CONFIG
# =========================================================

@router.put("/{client_id}/widget-config")
async def save_client_widget_config(
    client_id: str,
    request: WidgetConfigRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:

    requested_client_id = client_id.strip()

    if current_user.get("role") != "admin":

        own_client_id = current_user.get(
            "client_id"
        )

        if requested_client_id != own_client_id:

            raise HTTPException(
                status_code=403,
                detail="You do not have access to this client.",
            )

    client = await get_client(
        requested_client_id
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    widget_config = normalize_widget_config(
        request
    )

    updated_client = await update_widget_config(
        requested_client_id,
        widget_config,
    )

    if not updated_client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    saved_config = {
        **DEFAULT_WIDGET_CONFIG,
        **widget_config,
    }

    return {
        "message": "Widget branding saved successfully.",
        "client_id": requested_client_id,
        "config": saved_config,
    }


# =========================================================
# UPDATE CLIENT
# =========================================================

@router.patch("/me")
async def update_my_client(
    request: ClientUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:

    client_id = current_user.get(
        "client_id"
    )

    if not client_id:

        raise HTTPException(
            status_code=404,
            detail="No client is assigned to this user.",
        )

    update_data = {}

    if request.business_name is not None:

        business_name = (
            request.business_name.strip()
        )

        if not business_name:

            raise HTTPException(
                status_code=400,
                detail="business_name cannot be empty.",
            )

        update_data[
            "business_name"
        ] = business_name

    if request.agent_name is not None:

        agent_name = (
            request.agent_name.strip()
        )

        if not agent_name:

            raise HTTPException(
                status_code=400,
                detail="agent_name cannot be empty.",
            )

        update_data[
            "agent_name"
        ] = agent_name

    if request.website is not None:

        update_data[
            "website"
        ] = request.website.strip()

    if not update_data:

        raise HTTPException(
            status_code=400,
            detail="No fields were provided for update.",
        )

    update_data["updated_at"] = datetime.now(
        timezone.utc
    )

    await clients_collection.update_one(
        {
            "client_id": client_id,
        },
        {
            "$set": update_data,
        },
    )

    updated_client = await get_client(
        client_id
    )

    if not updated_client:

        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    updated_client.pop("_id", None)

    return updated_client