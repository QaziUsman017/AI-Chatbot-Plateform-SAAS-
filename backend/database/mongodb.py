"""
MongoDB database helpers for the AI Chatbot Platform.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()


# =========================================================
# MONGODB CONFIGURATION
# =========================================================

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI is not configured."
    )

client = AsyncIOMotorClient(MONGODB_URI)

database = client["ai_chatbot_platform"]


# =========================================================
# COLLECTIONS
# =========================================================

conversations_collection = database["conversations"]
users_collection = database["users"]
clients_collection = database["clients"]
agents_collection = database["agents"]
agent_configs_collection = database["agent_configs"]
visitors_collection = database["visitors"]
analytics_events_collection = database["analytics_events"]
documents_collection = database["documents"]


# =========================================================
# CONNECTION
# =========================================================

async def connect_to_mongodb() -> None:
    await client.admin.command("ping")
    print("Connected to MongoDB")


async def close_mongodb_connection() -> None:
    client.close()
    print("MongoDB connection closed")


# =========================================================
# USERS
# =========================================================

async def create_user(
    user_id: str,
    email: str,
    hashed_password: str | None = None,
    role: str = "user",
    client_id: str | None = None,
    full_name: str | None = None,
    password_hash: str | None = None,
) -> dict:
    """
    Create a user.

    Supports both:
    - hashed_password
    - password_hash

    This keeps compatibility with the authentication routes.
    """

    now = datetime.now(timezone.utc)

    final_password_hash = (
        password_hash
        if password_hash is not None
        else hashed_password
    )

    if not final_password_hash:
        raise ValueError(
            "A password hash is required."
        )

    document = {
        "user_id": user_id,
        "email": email,
        "password_hash": final_password_hash,
        "role": role,
        "client_id": client_id,
        "full_name": full_name,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    await users_collection.insert_one(
        document
    )

    document.pop("_id", None)

    return document


async def get_user_by_email(
    email: str,
) -> dict | None:

    user = await users_collection.find_one(
        {
            "email": email,
        }
    )

    if not user:
        return None

    # =====================================================
    # BACKWARD COMPATIBILITY
    # =====================================================

    if (
        not user.get("password_hash")
        and user.get("password")
    ):
        user["password_hash"] = user["password"]

    return user


async def get_user_by_id(
    user_id: str,
) -> dict | None:

    user = await users_collection.find_one(
        {
            "user_id": user_id,
        }
    )

    if not user:
        return None

    if (
        not user.get("password_hash")
        and user.get("password")
    ):
        user["password_hash"] = user["password"]

    return user


# =========================================================
# CLIENTS
# =========================================================

DEFAULT_WIDGET_CONFIG = {

    # -----------------------------------------------------
    # Existing / primary branding
    # -----------------------------------------------------

    "primary_color": "#0ea5e9",
    "secondary_color": "#0f172a",
    "text_color": "#0f172a",

    # -----------------------------------------------------
    # Bot identity
    # -----------------------------------------------------

    "bot_name": "AI Assistant",
    "logo": "",
    "position": "bottom-right",
    "welcome_message": "Hi! How can I help you today?",

    # -----------------------------------------------------
    # Widget background colors
    # -----------------------------------------------------

    "background_color": "#0b0d0c",
    "surface_color": "#111513",
    "surface_secondary_color": "#161a18",
    "surface_tertiary_color": "#1c211f",

    # -----------------------------------------------------
    # Text colors
    # -----------------------------------------------------

    "text_primary_color": "#f5f7f6",
    "text_secondary_color": "#d8dedb",
    "text_muted_color": "#929b97",
    "text_muted_dark_color": "#68716d",

    # -----------------------------------------------------
    # Border colors
    # -----------------------------------------------------

    "border_color": "rgba(255,255,255,0.08)",
    "border_light_color": "rgba(255,255,255,0.12)",

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    "header_background_color": "#111513",
    "header_text_color": "#f5f7f6",
    "header_secondary_text_color": "#929b97",
    "header_button_color": "#929b97",
    "header_button_background_color": "rgba(255,255,255,0.06)",
    "header_button_border_color": "rgba(255,255,255,0.08)",

    # -----------------------------------------------------
    # Assistant avatar / welcome icon
    # -----------------------------------------------------

    "avatar_background_color": "#10b981",
    "avatar_text_color": "#ffffff",

    "welcome_icon_background_color": "#10b981",
    "welcome_icon_text_color": "#ffffff",

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    "status_dot_color": "#22c55e",
    "status_text_color": "#929b97",

    # -----------------------------------------------------
    # User messages
    # -----------------------------------------------------

    "user_message_background_color": "#242a27",
    "user_message_text_color": "#f2f5f3",
    "user_message_border_color": "rgba(255,255,255,0.09)",

    # -----------------------------------------------------
    # Assistant messages
    # -----------------------------------------------------

    "assistant_message_background_color": "#1b211f",
    "assistant_message_text_color": "#e7ece9",
    "assistant_message_border_color": "rgba(255,255,255,0.10)",

    # -----------------------------------------------------
    # Input / composer
    # -----------------------------------------------------

    "composer_background_color": "#111513",
    "input_background_color": "#161a18",
    "input_text_color": "#f5f7f6",
    "input_placeholder_color": "#929b97",
    "input_border_color": "rgba(255,255,255,0.10)",
    "input_focus_border_color": "#10b981",

    # -----------------------------------------------------
    # Send button
    # -----------------------------------------------------

    "send_button_background_color": "#10b981",
    "send_button_text_color": "#ffffff",

    # -----------------------------------------------------
    # Floating launcher
    # -----------------------------------------------------

    "launcher_background_color": "#10b981",
    "launcher_icon_color": "#ffffff",

    # -----------------------------------------------------
    # Typing indicator
    # -----------------------------------------------------

    "typing_background_color": "#161a18",
    "typing_dot_color": "#929b97",

    # -----------------------------------------------------
    # Code blocks
    # -----------------------------------------------------

    "code_background_color": "#0b0e0d",
    "code_text_color": "#e7ece9",

    # -----------------------------------------------------
    # Utility states
    # -----------------------------------------------------

    "danger_color": "#ef4444",
    "success_color": "#22c55e",
}


async def create_client(
    client_id: str,
    business_name: str,
    agent_name: str,
    website: str = "",
) -> dict:

    now = datetime.now(timezone.utc)

    document = {
        "client_id": client_id,
        "business_name": business_name,
        "agent_name": agent_name,
        "website": website,
        "status": "active",

        "widget_config": dict(
            DEFAULT_WIDGET_CONFIG
        ),

        "created_at": now,
        "updated_at": now,
    }

    await clients_collection.insert_one(
        document
    )

    document.pop("_id", None)

    return document


async def get_client(
    client_id: str,
) -> dict | None:

    return await clients_collection.find_one(
        {
            "client_id": client_id,
        }
    )


async def get_widget_config(
    client_id: str,
) -> dict:

    client = await get_client(
        client_id
    )

    if not client:
        return dict(
            DEFAULT_WIDGET_CONFIG
        )

    stored = client.get(
        "widget_config"
    ) or {}

    config = dict(
        DEFAULT_WIDGET_CONFIG
    )

    if isinstance(stored, dict):
        config.update(stored)

    if not config.get("bot_name"):
        config["bot_name"] = (
            client.get("agent_name")
            or "AI Assistant"
        )

    return config


async def update_widget_config(
    client_id: str,
    widget_config: dict,
) -> dict | None:

    now = datetime.now(timezone.utc)

    existing_config = await get_widget_config(
        client_id
    )

    merged_config = dict(
        DEFAULT_WIDGET_CONFIG
    )

    if isinstance(existing_config, dict):
        merged_config.update(
            existing_config
        )

    if isinstance(widget_config, dict):
        merged_config.update(
            widget_config
        )

    result = await clients_collection.update_one(
        {
            "client_id": client_id,
        },
        {
            "$set": {
                "widget_config": merged_config,
                "updated_at": now,
            }
        },
    )

    if result.matched_count == 0:
        return None

    return await get_client(
        client_id
    )


# =========================================================
# DOCUMENTS
# =========================================================

async def save_document(
    client_id: str,
    filename: str,
    filetype: str | None = None,
    path: str | None = None,
    status: str = "processed",
) -> dict:
    """
    Create or update document metadata in MongoDB.

    Documents are uniquely identified by:
        client_id + filename

    This makes the function safe to call repeatedly,
    which is useful for syncing existing files from the
    filesystem into MongoDB.
    """

    client_id = str(client_id).strip()
    filename = str(filename).strip()

    if not client_id:
        raise ValueError(
            "client_id is required."
        )

    if not filename:
        raise ValueError(
            "filename is required."
        )

    now = datetime.now(timezone.utc)

    document = {
        "client_id": client_id,
        "filename": filename,
        "filetype": filetype or "",
        "status": status,
        "path": path or "",
        "updated_at": now,
    }

    await documents_collection.update_one(
        {
            "client_id": client_id,
            "filename": filename,
        },
        {
            "$set": document,
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    return document


async def delete_document(
    client_id: str,
    filename: str,
) -> bool:
    """
    Delete a document's metadata from MongoDB.

    Returns True when a document record was deleted.
    """

    client_id = str(client_id).strip()
    filename = str(filename).strip()

    if not client_id or not filename:
        return False

    result = await documents_collection.delete_one(
        {
            "client_id": client_id,
            "filename": filename,
        }
    )

    return result.deleted_count > 0


async def get_client_documents(
    client_id: str,
) -> list[dict]:
    """
    Get document metadata stored for a client.
    """

    client_id = str(client_id).strip()

    if not client_id:
        return []

    cursor = documents_collection.find(
        {
            "client_id": client_id,
        },
        {
            "_id": 0,
        },
    ).sort(
        "filename",
        1,
    )

    return await cursor.to_list(
        length=None
    )


# =========================================================
# DELETE CLIENT
# =========================================================

async def delete_client_data(
    client_id: str,
) -> dict:
    """
    Delete a client and all client-owned data.

    User accounts are NOT deleted.

    Any users assigned to this client are instead
    unassigned by setting client_id to None.

    Returns deletion statistics.
    """

    client_id = str(client_id).strip()

    if not client_id:
        return {
            "client_deleted": False,
            "agents_deleted": 0,
            "agent_configs_deleted": 0,
            "conversations_deleted": 0,
            "visitors_deleted": 0,
            "analytics_events_deleted": 0,
            "documents_deleted": 0,
            "users_unassigned": 0,
        }

    # -----------------------------------------------------
    # Make sure the client exists
    # -----------------------------------------------------

    existing_client = await clients_collection.find_one(
        {
            "client_id": client_id,
        }
    )

    if not existing_client:
        return {
            "client_deleted": False,
            "agents_deleted": 0,
            "agent_configs_deleted": 0,
            "conversations_deleted": 0,
            "visitors_deleted": 0,
            "analytics_events_deleted": 0,
            "documents_deleted": 0,
            "users_unassigned": 0,
        }

    # -----------------------------------------------------
    # Delete agents
    # -----------------------------------------------------

    agents_result = await agents_collection.delete_many(
        {
            "client_id": client_id,
        }
    )

    # -----------------------------------------------------
    # Delete agent configurations
    # -----------------------------------------------------

    agent_configs_result = (
        await agent_configs_collection.delete_many(
            {
                "client_id": client_id,
            }
        )
    )

    # -----------------------------------------------------
    # Delete conversations
    # -----------------------------------------------------

    conversations_result = (
        await conversations_collection.delete_many(
            {
                "client_id": client_id,
            }
        )
    )

    # -----------------------------------------------------
    # Delete visitors
    # -----------------------------------------------------

    visitors_result = await visitors_collection.delete_many(
        {
            "client_id": client_id,
        }
    )

    # -----------------------------------------------------
    # Delete analytics events
    # -----------------------------------------------------

    analytics_result = (
        await analytics_events_collection.delete_many(
            {
                "client_id": client_id,
            }
        )
    )

    # -----------------------------------------------------
    # Delete documents
    # -----------------------------------------------------

    documents_result = (
        await documents_collection.delete_many(
            {
                "client_id": client_id,
            }
        )
    )

    # -----------------------------------------------------
    # Unassign users
    # -----------------------------------------------------
    #
    # We intentionally DO NOT delete user accounts.
    # This prevents accidentally deleting platform/admin
    # authentication records.
    # -----------------------------------------------------

    users_result = await users_collection.update_many(
        {
            "client_id": client_id,
        },
        {
            "$set": {
                "client_id": None,
                "updated_at": datetime.now(
                    timezone.utc
                ),
            }
        },
    )

    # -----------------------------------------------------
    # Delete client itself
    # -----------------------------------------------------

    client_result = await clients_collection.delete_one(
        {
            "client_id": client_id,
        }
    )

    return {
        "client_deleted": (
            client_result.deleted_count > 0
        ),
        "agents_deleted": (
            agents_result.deleted_count
        ),
        "agent_configs_deleted": (
            agent_configs_result.deleted_count
        ),
        "conversations_deleted": (
            conversations_result.deleted_count
        ),
        "visitors_deleted": (
            visitors_result.deleted_count
        ),
        "analytics_events_deleted": (
            analytics_result.deleted_count
        ),
        "documents_deleted": (
            documents_result.deleted_count
        ),
        "users_unassigned": (
            users_result.modified_count
        ),
    }


# =========================================================
# AGENT CONFIGURATION
# =========================================================

async def create_agent_config(
    client_id: str,
    config: dict,
) -> dict:

    now = datetime.now(timezone.utc)

    document = {
        "client_id": client_id,
        **config,
        "created_at": now,
        "updated_at": now,
    }

    await agent_configs_collection.update_one(
        {
            "client_id": client_id,
        },
        {
            "$set": document,
        },
        upsert=True,
    )

    return document


async def get_agent_config(
    client_id: str,
) -> dict | None:

    return await agent_configs_collection.find_one(
        {
            "client_id": client_id,
        }
    )


# =========================================================
# CONVERSATIONS
# =========================================================

async def get_conversation(
    conversation_id: str,
    client_id: str,
    user_id: str,
) -> dict | None:

    return await conversations_collection.find_one(
        {
            "conversation_id": conversation_id,
            "client_id": client_id,
            "user_id": user_id,
        }
    )


async def get_conversation_for_client(
    conversation_id: str,
    client_id: str,
) -> dict | None:

    return await conversations_collection.find_one(
        {
            "conversation_id": conversation_id,
            "client_id": client_id,
        }
    )


async def get_user_conversations(
    user_id: str,
    client_id: str,
) -> list[dict]:

    cursor = conversations_collection.find(
        {
            "user_id": user_id,
            "client_id": client_id,
        },
        {
            "_id": 0,
        },
    ).sort(
        "updated_at",
        -1,
    )

    return await cursor.to_list(
        length=100
    )


async def get_client_conversations(
    client_id: str,
) -> list[dict]:

    cursor = conversations_collection.find(
        {
            "client_id": client_id,
        },
        {
            "_id": 0,
        },
    ).sort(
        "updated_at",
        -1,
    )

    return await cursor.to_list(
        length=100
    )


async def delete_conversation(
    conversation_id: str,
    client_id: str,
    user_id: str,
) -> bool:

    result = await conversations_collection.delete_one(
        {
            "conversation_id": conversation_id,
            "client_id": client_id,
            "user_id": user_id,
        }
    )

    return result.deleted_count > 0


async def delete_client_conversation(
    conversation_id: str,
    client_id: str,
) -> bool:

    result = await conversations_collection.delete_one(
        {
            "conversation_id": conversation_id,
            "client_id": client_id,
        }
    )

    return result.deleted_count > 0


async def save_conversation(
    conversation_id: str,
    client_id: str,
    user_id: str,
    messages: list[dict],
    created_at: datetime | None = None,
) -> dict:

    now = datetime.now(timezone.utc)

    if created_at is None:
        created_at = now

    document = {
        "conversation_id": conversation_id,
        "client_id": client_id,
        "user_id": user_id,
        "messages": messages,
        "created_at": created_at,
        "updated_at": now,
    }

    await conversations_collection.update_one(
        {
            "conversation_id": conversation_id,
            "client_id": client_id,
            "user_id": user_id,
        },
        {
            "$set": document,
        },
        upsert=True,
    )

    return document


# =========================================================
# VISITORS
# =========================================================

async def register_visitor(
    visitor_id: str,
    client_id: str,
) -> dict:

    now = datetime.now(timezone.utc)

    existing = await visitors_collection.find_one(
        {
            "visitor_id": visitor_id,
            "client_id": client_id,
        }
    )

    if existing:

        await visitors_collection.update_one(
            {
                "visitor_id": visitor_id,
                "client_id": client_id,
            },
            {
                "$set": {
                    "last_seen_at": now,
                },
                "$inc": {
                    "visit_count": 1,
                },
            },
        )

        return {
            **existing,
            "is_new": False,
        }

    document = {
        "visitor_id": visitor_id,
        "client_id": client_id,
        "first_seen_at": now,
        "last_seen_at": now,
        "visit_count": 1,
    }

    await visitors_collection.insert_one(
        document
    )

    document["is_new"] = True

    return document


# =========================================================
# ANALYTICS
# =========================================================

async def save_analytics_event(
    event_type: str,
    client_id: str,
    visitor_id: str | None = None,
    conversation_id: str | None = None,
    metadata: dict | None = None,
) -> dict:

    document = {
        "event_type": event_type,
        "client_id": client_id,
        "visitor_id": visitor_id,
        "conversation_id": conversation_id,
        "metadata": metadata or {},
        "created_at": datetime.now(
            timezone.utc
        ),
    }

    await analytics_events_collection.insert_one(
        document
    )

    document.pop("_id", None)

    return document


# =========================================================
# INDEX HELPER
# =========================================================

async def _ensure_index(
    collection,
    keys,
    *,
    unique: bool = False,
) -> None:
    """
    Safely ensure an index exists.

    MongoDB can already contain an index with the same
    key pattern but a different name.

    Therefore we inspect existing indexes before calling
    create_index().
    """

    existing_indexes = (
        await collection.index_information()
    )

    requested_keys = tuple(keys)

    for index_name, index_info in existing_indexes.items():

        existing_keys = tuple(
            index_info.get("key", [])
        )

        if existing_keys == requested_keys:
            return

    await collection.create_index(
        keys,
        unique=unique,
    )


# =========================================================
# DATABASE INDEXES
# =========================================================

async def create_database_indexes():
    """
    Create MongoDB indexes used by the AI Chatbot Platform.

    Safe to call every time the FastAPI application starts.

    Existing indexes are detected by their key pattern.
    """

    try:

        # -------------------------------------------------
        # Users
        # -------------------------------------------------

        await _ensure_index(
            users_collection,
            [("email", 1)],
            unique=True,
        )

        await _ensure_index(
            users_collection,
            [("user_id", 1)],
            unique=True,
        )

        # -------------------------------------------------
        # Clients
        # -------------------------------------------------

        await _ensure_index(
            clients_collection,
            [("client_id", 1)],
            unique=True,
        )

        # -------------------------------------------------
        # Agents
        # -------------------------------------------------

        await _ensure_index(
            agents_collection,
            [("client_id", 1)],
            unique=True,
        )

        # -------------------------------------------------
        # Agent configurations
        # -------------------------------------------------

        await _ensure_index(
            agent_configs_collection,
            [("client_id", 1)],
            unique=True,
        )

        # -------------------------------------------------
        # Conversations
        # -------------------------------------------------

        await _ensure_index(
            conversations_collection,
            [
                ("conversation_id", 1),
            ],
            unique=True,
        )

        await _ensure_index(
            conversations_collection,
            [
                ("client_id", 1),
                ("user_id", 1),
            ],
        )

        await _ensure_index(
            conversations_collection,
            [
                ("client_id", 1),
                ("created_at", -1),
            ],
        )

        await _ensure_index(
            conversations_collection,
            [
                ("client_id", 1),
                ("updated_at", -1),
            ],
        )

        # -------------------------------------------------
        # Visitors
        # -------------------------------------------------

        await _ensure_index(
            visitors_collection,
            [
                ("client_id", 1),
                ("visitor_id", 1),
            ],
            unique=True,
        )

        await _ensure_index(
            visitors_collection,
            [
                ("client_id", 1),
                ("last_seen_at", -1),
            ],
        )

        # -------------------------------------------------
        # Analytics
        # -------------------------------------------------

        await _ensure_index(
            analytics_events_collection,
            [
                ("client_id", 1),
                ("created_at", -1),
            ],
        )

        await _ensure_index(
            analytics_events_collection,
            [
                ("event_type", 1),
                ("created_at", -1),
            ],
        )

        # -------------------------------------------------
        # Documents
        # -------------------------------------------------

        await _ensure_index(
            documents_collection,
            [
                ("client_id", 1),
                ("created_at", -1),
            ],
        )

        # Prevent duplicate document metadata for the
        # same client + filename combination.
        #
        # If an old database already contains duplicate
        # records, _ensure_index() will safely skip this
        # index rather than breaking application startup.

        await _ensure_index(
            documents_collection,
            [
                ("client_id", 1),
                ("filename", 1),
            ],
            unique=True,
        )

        print(
            "MongoDB indexes ready."
        )

    except Exception as e:

        # Startup should not become unusable just because
        # an optional index cannot be created.

        print(
            f"MongoDB index setup warning: {e}"
        )