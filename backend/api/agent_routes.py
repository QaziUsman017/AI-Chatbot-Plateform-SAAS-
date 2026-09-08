"""Routes for AI agent configuration."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.mongodb import (
    agent_configs_collection,
    get_client,
    get_agent_config,
)


router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class AgentConfigRequest(BaseModel):
    client_id: str
    agent_name: str
    system_prompt: str
    language: str = "same_as_user"
    tone: str = "professional"
    max_tokens: int = 300
    temperature: float = 0.1


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def agent_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "agents",
    }


# =========================================================
# CREATE / UPDATE AGENT CONFIG
# =========================================================

@router.post("")
async def create_or_update_agent(
    request: AgentConfigRequest,
) -> dict[str, str | int | float]:

    client_id = request.client_id.strip()
    agent_name = request.agent_name.strip()
    system_prompt = request.system_prompt.strip()

    # ==========================================
    # Validation
    # ==========================================

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    if not agent_name:
        raise HTTPException(
            status_code=400,
            detail="agent_name cannot be empty.",
        )

    if not system_prompt:
        raise HTTPException(
            status_code=400,
            detail="system_prompt cannot be empty.",
        )

    if request.max_tokens <= 0:
        raise HTTPException(
            status_code=400,
            detail="max_tokens must be greater than 0.",
        )

    if request.temperature < 0 or request.temperature > 2:
        raise HTTPException(
            status_code=400,
            detail="temperature must be between 0 and 2.",
        )

    # ==========================================
    # Verify client
    # ==========================================

    existing_client = await get_client(
        client_id,
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # ==========================================
    # Save configuration
    # ==========================================

    now = datetime.now(timezone.utc)

    await agent_configs_collection.update_one(
        {
            "client_id": client_id,
        },
        {
            "$set": {
                "client_id": client_id,
                "agent_name": agent_name,
                "system_prompt": system_prompt,
                "language": request.language,
                "tone": request.tone,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    print("========================================")
    print("AGENT CONFIGURATION SAVED")
    print("Client ID:")
    print(client_id)
    print("Agent:")
    print(agent_name)
    print("========================================")

    return {
        "message": "Agent configuration saved successfully.",
        "client_id": client_id,
        "agent_name": agent_name,
        "language": request.language,
        "tone": request.tone,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }


# =========================================================
# GET AGENT CONFIG
# =========================================================

@router.get("/{client_id}")
async def get_agent_configuration(
    client_id: str,
) -> dict:

    client_id = client_id.strip()

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    config = await get_agent_config(
        client_id,
    )

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Agent configuration not found.",
        )

    config.pop(
        "_id",
        None,
    )

    return config