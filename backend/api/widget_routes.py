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

    # -----------------------------------------------------
    # Normalize request
    # -----------------------------------------------------

    message = request.message.strip()

    client_id = request.client_id.strip()

    visitor_id = request.visitor_id.strip()

    conversation_id = (
        request.conversation_id.strip()
        if request.conversation_id
        else ""
    )

    # -----------------------------------------------------
    # Validate request
    # -----------------------------------------------------

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
    # Create conversation ID
    # -----------------------------------------------------

    if not conversation_id:
        conversation_id = str(
            uuid4()
        )

    # -----------------------------------------------------
    # Register visitor
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Fallback to frontend history
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Clean history
    #
    # Only send valid role/content pairs
    # to the AI service.
    # -----------------------------------------------------

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
    # RAG
    # =====================================================

    context = ""

    try:

        chunks = await retrieve_chunks(
            query=message,
            client_id=client_id,
        )

        if chunks:

            context = "\n\n".join(
                str(chunk)
                for chunk in chunks
            )

    except TypeError:

        # Compatibility fallback for an older
        # retrieve_chunks positional signature.
        try:

            chunks = await retrieve_chunks(
                message,
                client_id,
            )

            if chunks:

                context = "\n\n".join(
                    str(chunk)
                    for chunk in chunks
                )

        except Exception as exc:

            print(
                "RAG retrieval fallback failed:",
                repr(exc),
            )

            context = ""

    except Exception as exc:

        print(
            "RAG retrieval failed:",
            repr(exc),
        )

        context = ""

    # =====================================================
    # AI RESPONSE
    # =====================================================

    try:

        # IMPORTANT:
        #
        # generate_response() accepts:
        #
        #   message
        #   conversation_history
        #   context
        #   agent_config
        #
        # Do NOT pass client_id or history here.
        #

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

    # -----------------------------------------------------
    # Normalize AI response
    # -----------------------------------------------------

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