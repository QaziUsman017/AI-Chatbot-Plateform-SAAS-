"""
Public widget routes.

These routes are intentionally public because they are consumed
by client websites through the embedded chatbot widget.
"""

from __future__ import annotations

import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.database.mongodb import (
    get_agent_config,
    get_client,
    get_conversation,
    get_widget_config,
    register_visitor,
    save_analytics_event,
    save_conversation,
)

from backend.services.ai_service import generate_response
from backend.services.rag.retrieval import retrieve_chunks


router = APIRouter(
    prefix="/widget",
    tags=["widget"],
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FRONTEND_DIR = BASE_DIR / "frontend"

FRONTEND_INDEX = FRONTEND_DIR / "index.html"
FRONTEND_LOGIN = FRONTEND_DIR / "login.html"

FRONTEND_CSS = FRONTEND_DIR / "css"
FRONTEND_JS = FRONTEND_DIR / "js"

WIDGET_DIR = FRONTEND_DIR / "widget"

WIDGET_HTML = WIDGET_DIR / "widget.html"


# =========================================================
# REQUEST MODELS
# =========================================================

class WidgetVisitRequest(BaseModel):
    visitor_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    client_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class WidgetChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    client_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    visitor_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    conversation_id: str = ""

    conversation_history: list[dict[str, str]] = []


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def widget_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "widget",
    }


# =========================================================
# PUBLIC WIDGET CONFIG
# =========================================================

@router.get("/config")
async def get_public_widget_config(
    client_id: str,
) -> dict:

    client_id = client_id.strip()

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id is required.",
        )

    # -----------------------------------------------------
    # Validate client
    # -----------------------------------------------------

    client = await get_client(
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # -----------------------------------------------------
    # Load widget configuration
    # -----------------------------------------------------

    config = await get_widget_config(
        client_id
    )

    if not isinstance(config, dict):
        config = {}

    # -----------------------------------------------------
    # Load agent configuration
    # -----------------------------------------------------

    agent_config = await get_agent_config(
        client_id
    )

    if isinstance(agent_config, dict):

        agent_name = (
            agent_config.get("agent_name")
            or client.get("agent_name")
            or "AI Assistant"
        )

    else:

        agent_name = (
            client.get("agent_name")
            or "AI Assistant"
        )

    agent_name = str(
        agent_name
    ).strip()

    if not agent_name:
        agent_name = "AI Assistant"

    # -----------------------------------------------------
    # Make agent name available to widget
    # -----------------------------------------------------

    config["agent_name"] = agent_name
    config["bot_name"] = agent_name

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "client_id": client_id,
        "config": config,
    }


# =========================================================
# WIDGET VISIT
# =========================================================

@router.post("/visit")
async def widget_visit(
    request: WidgetVisitRequest,
) -> dict:

    visitor_id = request.visitor_id.strip()

    client_id = request.client_id.strip()

    if not visitor_id:
        raise HTTPException(
            status_code=400,
            detail="visitor_id is required.",
        )

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id is required.",
        )

    # -----------------------------------------------------
    # Validate client
    # -----------------------------------------------------

    client = await get_client(
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # -----------------------------------------------------
    # Register visitor
    # -----------------------------------------------------

    visitor = await register_visitor(
        visitor_id=visitor_id,
        client_id=client_id,
    )

    # -----------------------------------------------------
    # Analytics
    # -----------------------------------------------------

    await save_analytics_event(
        event_type="visit",
        client_id=client_id,
        visitor_id=visitor_id,
        metadata={
            "new_visitor": visitor.get(
                "is_new",
                False,
            )
        },
    )

    return {
        "status": "ok",
        "client_id": client_id,
        "visitor_id": visitor_id,
        "is_new_visitor": visitor.get(
            "is_new",
            False,
        ),
    }


# =========================================================
# WIDGET FRAME
# =========================================================

@router.get("/frame")
async def widget_frame(
    client_id: str,
):

    client_id = client_id.strip()

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id is required.",
        )

    # -----------------------------------------------------
    # Validate client
    # -----------------------------------------------------

    client = await get_client(
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # -----------------------------------------------------
    # Check widget HTML
    # -----------------------------------------------------

    if not WIDGET_HTML.exists():
        raise HTTPException(
            status_code=404,
            detail="Widget HTML not found.",
        )

    return FileResponse(
        path=WIDGET_HTML,
        media_type="text/html",
        headers={
            "Cache-Control": (
                "no-store, "
                "no-cache, "
                "must-revalidate"
            ),
            "Pragma": "no-cache",
        },
    )


# =========================================================
# WIDGET CHAT
# =========================================================

@router.post("/chat")
async def widget_chat(
    request: WidgetChatRequest,
) -> dict:

    started_at = time.perf_counter()

    # =====================================================
    # NORMALIZE REQUEST
    # =====================================================

    message = request.message.strip()

    client_id = request.client_id.strip()

    visitor_id = request.visitor_id.strip()

    conversation_id = (
        request.conversation_id.strip()
        if request.conversation_id
        else ""
    )

    # =====================================================
    # VALIDATE REQUEST
    # =====================================================

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id is required.",
        )

    if not visitor_id:
        raise HTTPException(
            status_code=400,
            detail="visitor_id is required.",
        )

    # =====================================================
    # VALIDATE CLIENT
    # =====================================================

    client = await get_client(
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # =====================================================
    # CREATE CONVERSATION ID
    # =====================================================

    if not conversation_id:
        conversation_id = str(
            uuid4()
        )

    # =====================================================
    # REGISTER VISITOR
    # =====================================================

    await register_visitor(
        visitor_id=visitor_id,
        client_id=client_id,
    )

    # =====================================================
    # AGENT CONFIG
    # =====================================================

    agent_config = await get_agent_config(
        client_id
    )

    if not isinstance(
        agent_config,
        dict,
    ):
        agent_config = {}

    # -----------------------------------------------------
    # Default agent configuration
    # -----------------------------------------------------

    if not agent_config:

        agent_config = {
            "agent_name": (
                client.get("agent_name")
                or "AI Assistant"
            ),

            "system_prompt": (
                "You are a helpful AI assistant."
            ),

            "language": "English",

            "tone": "Professional",

            "max_tokens": 1024,

            "temperature": 0.7,
        }

    # -----------------------------------------------------
    # Make sure agent name always exists
    # -----------------------------------------------------

    if not agent_config.get(
        "agent_name"
    ):

        agent_config["agent_name"] = (
            client.get("agent_name")
            or "AI Assistant"
        )

    # =====================================================
    # EXISTING CONVERSATION
    # =====================================================

    existing_conversation = (
        await get_conversation(
            conversation_id=conversation_id,
            client_id=client_id,
            user_id=visitor_id,
        )
    )

    history = []

    if isinstance(
        existing_conversation,
        dict,
    ):

        existing_messages = (
            existing_conversation.get(
                "messages",
                [],
            )
        )

        if isinstance(
            existing_messages,
            list,
        ):
            history = existing_messages

    # =====================================================
    # FALLBACK TO FRONTEND HISTORY
    # =====================================================

    if not history:

        request_history = (
            request.conversation_history
            or []
        )

        if isinstance(
            request_history,
            list,
        ):
            history = request_history

    # =====================================================
    # CLEAN HISTORY
    # =====================================================

    cleaned_history = []

    for item in history:

        if not isinstance(
            item,
            dict,
        ):
            continue

        role = str(
            item.get(
                "role",
                "",
            )
        ).strip()

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if role not in {
            "user",
            "assistant",
        }:
            continue

        if not content:
            continue

        cleaned_history.append(
            {
                "role": role,
                "content": content,
            }
        )

    history = cleaned_history

    # =====================================================
    # RAG RETRIEVAL
    # =====================================================

    context = ""

    print("========================================")
    print("WIDGET RAG RETRIEVAL")
    print("========================================")
    print("QUERY:")
    print(repr(message))
    print("CLIENT ID:")
    print(repr(client_id))
    print("LIMIT:")
    print(5)
    print("========================================")

    try:

        # IMPORTANT:
        #
        # retrieve_chunks() is SYNCHRONOUS.
        #
        # Do NOT use:
        #
        #     await retrieve_chunks(...)
        #
        # Also use named arguments so client_id can never
        # accidentally be passed as the limit parameter.

        chunks = retrieve_chunks(
            query=message,
            limit=5,
            client_id=client_id,
        )

        if not isinstance(
            chunks,
            list,
        ):
            print(
                "RAG: retrieve_chunks() did not return a list."
            )
            chunks = []

        print("========================================")
        print("WIDGET RAG RESULT")
        print("CHUNK COUNT:")
        print(len(chunks))
        print("========================================")

        # -------------------------------------------------
        # Build clean AI context.
        #
        # Only the actual chunk text is sent to the AI.
        # -------------------------------------------------

        context_parts = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            if not isinstance(
                chunk,
                dict,
            ):
                print(
                    f"RAG: Skipping invalid chunk #{index}."
                )
                continue

            text = str(
                chunk.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                print(
                    f"RAG: Skipping empty chunk #{index}."
                )
                continue

            context_parts.append(
                text
            )

        context = "\n\n".join(
            context_parts
        )

    except Exception as exc:

        print("========================================")
        print("WIDGET RAG RETRIEVAL ERROR")
        print("========================================")
        print("TYPE:")
        print(type(exc).__name__)
        print("ERROR:")
        print(repr(exc))
        print("========================================")

        context = ""

    # =====================================================
    # RAG CONTEXT LOG
    # =====================================================

    print("========================================")
    print("WIDGET RAG CONTEXT")
    print("========================================")
    print("AVAILABLE:")
    print(bool(context.strip()))
    print("LENGTH:")
    print(len(context))
    print("CONTENT:")
    print(repr(context[:3000]))
    print("========================================")

    # =====================================================
    # AI RESPONSE
    # =====================================================

    try:

        response = await generate_response(
            message=message,
            conversation_history=history,
            context=context,
            agent_config=agent_config,
        )

    except Exception as exc:

        print(
            "AI response generation failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI response generation failed. "
                "Please check the backend logs."
            ),
        ) from exc

    # =====================================================
    # NORMALIZE AI RESPONSE
    # =====================================================

    if isinstance(
        response,
        dict,
    ):

        assistant_message = (
            response.get("response")
            or response.get("answer")
            or response.get("message")
            or str(response)
        )

    else:

        assistant_message = str(
            response
        )

    assistant_message = (
        assistant_message.strip()
    )

    if not assistant_message:

        assistant_message = (
            "AI ne koi response generate nahi kiya."
        )

    # =====================================================
    # RESPONSE TIME
    # =====================================================

    response_time_ms = round(
        (
            time.perf_counter()
            - started_at
        )
        * 1000
    )

    # =====================================================
    # SAVE CONVERSATION
    # =====================================================

    messages = list(history)

    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    messages.append(
        {
            "role": "assistant",
            "content": assistant_message,
        }
    )

    await save_conversation(
        conversation_id=conversation_id,
        client_id=client_id,
        user_id=visitor_id,
        messages=messages,
    )

    # =====================================================
    # ANALYTICS
    # =====================================================

    await save_analytics_event(
        event_type="message",
        client_id=client_id,
        visitor_id=visitor_id,
        conversation_id=conversation_id,
        metadata={
            "response_time_ms": response_time_ms,
        },
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "response": assistant_message,
        "client_id": client_id,
        "visitor_id": visitor_id,
        "conversation_id": conversation_id,
        "response_time_ms": response_time_ms,
    }


# =========================================================
# STATIC WIDGET FILES
# =========================================================

@router.get("/widget-loader.js")
async def widget_loader():

    file = (
        WIDGET_DIR
        / "widget-loader.js"
    )

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="widget-loader.js not found.",
        )

    return FileResponse(
        path=file,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/widget.js")
async def widget_script():

    file = (
        WIDGET_DIR
        / "widget.js"
    )

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="widget.js not found.",
        )

    return FileResponse(
        path=file,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/iframe-manager.js")
async def iframe_manager():

    file = (
        WIDGET_DIR
        / "iframe-manager.js"
    )

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="iframe-manager.js not found.",
        )

    return FileResponse(
        path=file,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/css/{filename}")
async def widget_css(
    filename: str,
):

    file = (
        WIDGET_DIR
        / "css"
        / filename
    )

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="Widget CSS file not found.",
        )

    return FileResponse(
        path=file,
        media_type="text/css",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/js/{filename}")
async def widget_js(
    filename: str,
):

    file = (
        WIDGET_DIR
        / "js"
        / filename
    )

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="Widget JS file not found.",
        )

    return FileResponse(
        path=file,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


# =========================================================
# LOGIN
# =========================================================

@router.get("/login.html")
async def widget_login():

    if not FRONTEND_LOGIN.exists():
        raise HTTPException(
            status_code=404,
            detail="Login page not found.",
        )

    return FileResponse(
        path=FRONTEND_LOGIN,
        media_type="text/html",
    )