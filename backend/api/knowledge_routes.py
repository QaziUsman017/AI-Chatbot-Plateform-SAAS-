"""Placeholder routes for knowledge-base operations."""

from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/health")
async def knowledge_health() -> dict[str, str]:
    return {"status": "ok", "module": "knowledge"}
