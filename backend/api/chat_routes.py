"""Routes for client-specific chat interactions."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.auth_routes import get_current_user

from backend.database.mongodb import (
    get_agent_config,
    get_conversation,
    get_conversation_for_client,
    get_client_conversations,
    delete_client_conversation,
    save_conversation,
)

from backend.services.ai_service import generate_response

from backend.services.rag.retrieval import retrieve_chunks


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class RetrievalRequest(BaseModel):
    query: str
    client_id: str
    limit: int = 5


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def chat_health() -> dict[str, str]:

    return {
        "status": "ok",
        "module": "chat",
    }


# =========================================================
# CHAT HISTORY
# =========================================================

@router.get("/history")
async def chat_history(
    current_user: dict = Depends(get_current_user),
) -> dict:

    client_id = current_user.get("client_id")

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    client_id = client_id.strip()

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="Invalid client ID.",
        )

    conversations = await get_client_conversations(
        client_id=client_id,
    )

    return {
        "client_id": client_id,
        "conversations": conversations,
    }


# =========================================================
# GET SINGLE CONVERSATION
# =========================================================

@router.get("/{conversation_id}")
async def get_single_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:

    client_id = current_user.get("client_id")

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    conversation_id = conversation_id.strip()
    client_id = client_id.strip()

    if not conversation_id:
        raise HTTPException(
            status_code=400,
            detail="Conversation ID cannot be empty.",
        )

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="Invalid client ID.",
        )

    conversation = await get_conversation_for_client(
        conversation_id=conversation_id,
        client_id=client_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    conversation.pop(
        "_id",
        None,
    )

    return conversation


# =========================================================
# DELETE CONVERSATION
# =========================================================

@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:

    client_id = current_user.get("client_id")

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    conversation_id = conversation_id.strip()
    client_id = client_id.strip()

    if not conversation_id:
        raise HTTPException(
            status_code=400,
            detail="Conversation ID cannot be empty.",
        )

    deleted = await delete_client_conversation(
        conversation_id=conversation_id,
        client_id=client_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }


# =========================================================
# CHAT
# =========================================================

@router.post("")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:

    print("========================================")
    print("AUTHENTICATED CLIENT-SPECIFIC CHAT")
    print("========================================")

    # =========================================================
    # GET AUTHENTICATED USER
    # =========================================================

    user_id = current_user.get("user_id")
    client_id = current_user.get("client_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID not found.",
        )

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    user_id = user_id.strip()
    client_id = client_id.strip()

    # =========================================================
    # VALIDATE MESSAGE
    # =========================================================

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # =========================================================
    # LOAD AGENT CONFIGURATION
    # =========================================================

    agent_config = await get_agent_config(
        client_id,
    )

    if not agent_config:
        raise HTTPException(
            status_code=404,
            detail="Agent configuration not found for this client.",
        )

    agent_config.pop(
        "_id",
        None,
    )

    print("========================================")
    print("AGENT CONFIGURATION LOADED")
    print("Client ID:")
    print(client_id)
    print("Agent Name:")
    print(agent_config.get("agent_name"))
    print("========================================")

    # =========================================================
    # CONVERSATION ID
    # =========================================================

    conversation_id = request.conversation_id

    if conversation_id:
        conversation_id = conversation_id.strip()

    if not conversation_id:

        conversation_id = str(uuid4())

        print("========================================")
        print("NEW CONVERSATION")
        print("Conversation ID:")
        print(conversation_id)
        print("User ID:")
        print(user_id)
        print("Client ID:")
        print(client_id)
        print("========================================")

    # =========================================================
    # LOAD CONVERSATION FROM MONGODB
    # =========================================================

    stored_conversation = await get_conversation(
        conversation_id=conversation_id,
        client_id=client_id,
        user_id=user_id,
    )

    # =========================================================
    # PREVENT ACCESS TO ANOTHER CONVERSATION
    # =========================================================

    if request.conversation_id and not stored_conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # =========================================================
    # GET PREVIOUS MESSAGES
    # =========================================================

    conversation_history: list[dict[str, str]] = []

    if stored_conversation:

        for stored_message in stored_conversation.get(
            "messages",
            [],
        ):

            if not isinstance(
                stored_message,
                dict,
            ):
                continue

            role = stored_message.get("role")
            content = stored_message.get("content")

            if role and content:

                conversation_history.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

    print("========================================")
    print("CONVERSATION HISTORY")
    print("Messages:")
    print(len(conversation_history))
    print("Conversation ID:")
    print(conversation_id)
    print("========================================")

    # =========================================================
    # RAG RETRIEVAL
    # =========================================================

    print("========================================")
    print("STARTING RAG RETRIEVAL")
    print("Query:")
    print(repr(message))
    print("Client ID:")
    print(repr(client_id))
    print("========================================")

    chunks = retrieve_chunks(
        message,
        limit=5,
        client_id=client_id,
    )

    print("========================================")
    print("CHAT RAG RESULTS")
    print("Chunk count:")
    print(len(chunks))
    print("========================================")

    # =========================================================
    # BUILD RAG CONTEXT
    # =========================================================

    context_parts: list[str] = []

    for chunk in chunks:

        text = str(
            chunk.get(
                "text",
                "",
            )
        ).strip()

        if text:
            context_parts.append(
                text
            )

    context = "\n\n".join(
        context_parts
    )

    print("========================================")
    print("RAG CONTEXT")
    print("Available:")
    print(bool(context.strip()))
    print("Length:")
    print(len(context))
    print("Content:")
    print(repr(context[:3000]))
    print("========================================")

    # =========================================================
    # GENERATE AI RESPONSE
    # =========================================================

    response = await generate_response(
        message,
        conversation_history,
        context=context,
        agent_config=agent_config,
    )

    print("========================================")
    print("FINAL RESPONSE:")
    print(repr(response))
    print("========================================")

    # =========================================================
    # PREPARE NEW MESSAGES
    # =========================================================

    now = datetime.now(
        timezone.utc
    )

    user_message = {
        "role": "user",
        "content": message,
        "created_at": now,
    }

    assistant_message = {
        "role": "assistant",
        "content": response,
        "created_at": now,
    }

    # =========================================================
    # BUILD COMPLETE CONVERSATION
    # =========================================================

    updated_messages: list[dict] = []

    if stored_conversation:

        existing_messages = stored_conversation.get(
            "messages",
            [],
        )

        if isinstance(
            existing_messages,
            list,
        ):

            updated_messages = list(
                existing_messages
            )

    updated_messages.append(
        user_message
    )

    updated_messages.append(
        assistant_message
    )

    # =========================================================
    # SAVE COMPLETE CONVERSATION
    # =========================================================

    try:

        await save_conversation(
            conversation_id=conversation_id,
            client_id=client_id,
            user_id=user_id,
            messages=updated_messages,
            created_at=(
                stored_conversation.get(
                    "created_at"
                )
                if stored_conversation
                else now
            ),
        )

        print("========================================")
        print("MONGODB")
        print("Conversation saved successfully")
        print("Conversation ID:")
        print(conversation_id)
        print("User ID:")
        print(user_id)
        print("Client ID:")
        print(client_id)
        print("Total messages saved:")
        print(len(updated_messages))
        print("========================================")

    except Exception as error:

        print("========================================")
        print("MONGODB ERROR")
        print(error)
        print("========================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to save conversation.",
        )

    # =========================================================
    # RESPONSE
    # =========================================================

    return {
        "response": response,
        "conversation_id": conversation_id,
        "client_id": client_id,
    }


# =========================================================
# RESET CHAT
# =========================================================

@router.post("/reset")
async def reset_chat(
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:

    user_id = current_user.get("user_id")
    client_id = current_user.get("client_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID not found.",
        )

    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    new_conversation_id = str(uuid4())

    return {
        "message": "New conversation started successfully.",
        "conversation_id": new_conversation_id,
    }


# =========================================================
# RETRIEVE
# =========================================================

@router.post("/retrieve")
async def retrieve(
    request: RetrievalRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:

    authenticated_client_id = current_user.get(
        "client_id"
    )

    if not authenticated_client_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with a client.",
        )

    authenticated_client_id = (
        authenticated_client_id.strip()
    )

    # =========================================================
    # SECURITY CHECK
    # =========================================================

    if (
        request.client_id.strip()
        != authenticated_client_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You are not authorized to access "
                "this client's knowledge base."
            ),
        )

    if not request.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    # =========================================================
    # RAG RETRIEVAL
    # =========================================================

    chunks = retrieve_chunks(
        request.query,
        request.limit,
        client_id=authenticated_client_id,
    )

    return {
        "query": request.query,
        "client_id": authenticated_client_id,
        "results": chunks,
    }