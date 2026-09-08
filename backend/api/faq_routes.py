"""Routes for client-specific FAQ knowledge."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.rag.rag_service import index_text


router = APIRouter(
    prefix="/faq",
    tags=["faq"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class FAQRequest(BaseModel):
    question: str
    answer: str
    client_id: str


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def faq_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "faq",
    }


# =========================================================
# CREATE FAQ
# =========================================================

@router.post("")
async def create_faq(
    request: FAQRequest,
) -> dict[str, str | int]:

    question = request.question.strip()
    answer = request.answer.strip()
    client_id = request.client_id.strip()

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="FAQ question cannot be empty.",
        )

    if not answer:
        raise HTTPException(
            status_code=400,
            detail="FAQ answer cannot be empty.",
        )

    faq_text = (
        f"FAQ QUESTION:\n"
        f"{question}\n\n"
        f"FAQ ANSWER:\n"
        f"{answer}"
    )

    try:
        chunks_indexed = index_text(
            faq_text,
            source="faq",
            client_id=client_id,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not index FAQ: {error}",
        ) from error

    return {
        "message": "FAQ added successfully.",
        "client_id": client_id,
        "chunks_indexed": chunks_indexed,
    }