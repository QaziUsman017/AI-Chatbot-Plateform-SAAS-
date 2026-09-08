"""Analytics service for MongoDB-backed dashboard analytics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from backend.database.mongodb import (
    clients_collection,
    conversations_collection,
    documents_collection,
    visitors_collection,
)


# =========================================================
# HELPERS
# =========================================================

def _message_count_from_conversations(
    conversations: list[dict],
) -> int:

    total = 0

    for conversation in conversations:

        messages = conversation.get(
            "messages",
            [],
        )

        if isinstance(messages, list):
            total += len(messages)

    return total


def _response_times(
    conversations: list[dict],
) -> list[float]:

    values: list[float] = []

    for conversation in conversations:

        messages = conversation.get(
            "messages",
            [],
        )

        if not isinstance(messages, list):
            continue

        for message in messages:

            if not isinstance(message, dict):
                continue

            value = message.get(
                "response_time_ms"
            )

            if value is None:

                metadata = message.get(
                    "metadata"
                )

                if isinstance(metadata, dict):
                    value = metadata.get(
                        "response_time_ms"
                    )

            if value is None:
                continue

            try:

                number = float(value)

                if number >= 0:
                    values.append(number)

            except (
                TypeError,
                ValueError,
            ):
                continue

    return values


async def _get_valid_client_ids() -> set[str]:

    clients = await clients_collection.find(
        {},
        {
            "_id": 0,
            "client_id": 1,
        },
    ).to_list(
        length=None
    )

    return {
        str(client.get("client_id")).strip()
        for client in clients
        if client.get("client_id")
    }


# =========================================================
# MAIN ANALYTICS
# =========================================================

async def get_analytics(
    client_id: str | None = None,
) -> dict[str, Any]:

    # -----------------------------------------------------
    # DETERMINE CLIENT SCOPE
    # -----------------------------------------------------

    valid_client_ids = await _get_valid_client_ids()

    if client_id:

        client_id = client_id.strip()

        scoped_client_ids = {
            client_id
        }

    else:

        scoped_client_ids = valid_client_ids

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    if client_id:

        filters = {
            "client_id": client_id
        }

    else:

        filters = {
            "client_id": {
                "$in": list(scoped_client_ids)
            }
        }

    # -----------------------------------------------------
    # VISITORS
    # -----------------------------------------------------

    visitors = await visitors_collection.count_documents(
        filters
    )

    # -----------------------------------------------------
    # CONVERSATIONS
    # -----------------------------------------------------

    conversations_cursor = conversations_collection.find(
        filters,
        {
            "_id": 0,
            "client_id": 1,
            "messages": 1,
            "created_at": 1,
            "updated_at": 1,
        },
    )

    conversations = await conversations_cursor.to_list(
        length=None
    )

    conversation_count = len(
        conversations
    )

    # -----------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------

    message_count = (
        _message_count_from_conversations(
            conversations
        )
    )

    # -----------------------------------------------------
    # RESPONSE TIME
    # -----------------------------------------------------

    response_times = _response_times(
        conversations
    )

    if response_times:

        average_response_time = (
            sum(response_times)
            / len(response_times)
        )

    else:

        average_response_time = None

    # -----------------------------------------------------
    # DOCUMENTS
    # -----------------------------------------------------

    documents = await documents_collection.count_documents(
        filters
    )

    # -----------------------------------------------------
    # ACTIVE CLIENTS
    # -----------------------------------------------------

    thirty_days_ago = (
        datetime.now(timezone.utc)
        - timedelta(days=30)
    )

    active_client_filter = {
        "last_seen_at": {
            "$gte": thirty_days_ago
        }
    }

    if client_id:

        active_client_filter[
            "client_id"
        ] = client_id

    else:

        active_client_filter[
            "client_id"
        ] = {
            "$in": list(scoped_client_ids)
        }

    active_clients = len(
        await visitors_collection.distinct(
            "client_id",
            active_client_filter,
        )
    )

    # -----------------------------------------------------
    # DAILY ACTIVITY
    # -----------------------------------------------------

    daily_activity = (
        await get_daily_activity(
            client_id=client_id
        )
    )

    # -----------------------------------------------------
    # CLIENT ACTIVITY
    # -----------------------------------------------------

    client_activity = (
        await get_client_activity(
            client_id=client_id
        )
    )

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return {
        "visitors": visitors,

        "conversations": conversation_count,

        "messages": message_count,

        "response_time_ms": (
            round(
                average_response_time,
                2,
            )
            if average_response_time
            is not None
            else None
        ),

        "resolution_rate": None,

        "active_clients": active_clients,

        "documents": documents,

        "daily_activity": daily_activity,

        "client_activity": client_activity,

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# =========================================================
# DAILY ACTIVITY
# =========================================================

async def get_daily_activity(
    *,
    client_id: str | None = None,
    days: int = 7,
) -> list[dict[str, Any]]:

    now = datetime.now(timezone.utc)

    start_date = (
        datetime(
            now.year,
            now.month,
            now.day,
            tzinfo=timezone.utc,
        )
        - timedelta(days=days - 1)
    )

    end_date = (
        start_date
        + timedelta(days=days)
    )

    if client_id:

        visitor_filter = {
            "client_id": client_id,
            "first_seen_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        }

        conversation_filter = {
            "client_id": client_id,
            "created_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        }

    else:

        valid_client_ids = await _get_valid_client_ids()

        visitor_filter = {
            "client_id": {
                "$in": list(valid_client_ids)
            },
            "first_seen_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        }

        conversation_filter = {
            "client_id": {
                "$in": list(valid_client_ids)
            },
            "created_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        }

    # -----------------------------------------------------
    # VISITORS
    # -----------------------------------------------------

    visitor_records = (
        await visitors_collection.find(
            visitor_filter,
            {
                "_id": 0,
                "first_seen_at": 1,
            },
        ).to_list(
            length=None
        )
    )

    # -----------------------------------------------------
    # CONVERSATIONS
    # -----------------------------------------------------

    conversation_records = (
        await conversations_collection.find(
            conversation_filter,
            {
                "_id": 0,
                "created_at": 1,
                "messages": 1,
            },
        ).to_list(
            length=None
        )
    )

    # -----------------------------------------------------
    # BUILD DAILY DATA
    # -----------------------------------------------------

    result: list[dict[str, Any]] = []

    for offset in range(days):

        current_date = (
            start_date
            + timedelta(days=offset)
        )

        date_key = current_date.strftime(
            "%Y-%m-%d"
        )

        visitor_count = 0

        for visitor in visitor_records:

            created = visitor.get(
                "first_seen_at"
            )

            if not isinstance(
                created,
                datetime,
            ):
                continue

            if (
                created.date()
                == current_date.date()
            ):

                visitor_count += 1

        conversation_count = 0

        message_count = 0

        for conversation in conversation_records:

            created = conversation.get(
                "created_at"
            )

            if (
                isinstance(created, datetime)
                and created.date()
                == current_date.date()
            ):

                conversation_count += 1

                messages = conversation.get(
                    "messages",
                    [],
                )

                if isinstance(
                    messages,
                    list,
                ):

                    message_count += len(
                        messages
                    )

        result.append(
            {
                "date": date_key,

                "visitors": visitor_count,

                "conversations": conversation_count,

                "messages": message_count,

                "value": conversation_count,
            }
        )

    return result


# =========================================================
# CLIENT ACTIVITY
# =========================================================

async def get_client_activity(
    *,
    client_id: str | None = None,
) -> list[dict[str, Any]]:

    # =====================================================
    # SINGLE CLIENT
    # =====================================================

    if client_id:

        client = await clients_collection.find_one(
            {
                "client_id": client_id
            },
            {
                "_id": 0,
                "client_id": 1,
                "business_name": 1,
            },
        )

        if not client:
            return []

        visitor_count = (
            await visitors_collection.count_documents(
                {
                    "client_id": client_id
                }
            )
        )

        conversation_records = (
            await conversations_collection.find(
                {
                    "client_id": client_id
                },
                {
                    "_id": 0,
                    "messages": 1,
                },
            ).to_list(
                length=None
            )
        )

        conversation_count = len(
            conversation_records
        )

        message_count = (
            _message_count_from_conversations(
                conversation_records
            )
        )

        return [
            {
                "client_id": client_id,

                "name": (
                    client.get(
                        "business_name"
                    )
                    or client_id
                ),

                "visitors": visitor_count,

                "conversations": conversation_count,

                "messages": message_count,

                "status": "Active",
            }
        ]

    # =====================================================
    # ALL CLIENTS
    # =====================================================

    clients = await clients_collection.find(
        {},
        {
            "_id": 0,
            "client_id": 1,
            "business_name": 1,
        },
    ).to_list(
        length=None
    )

    result: list[dict[str, Any]] = []

    for client in clients:

        current_client_id = client.get(
            "client_id"
        )

        if not current_client_id:
            continue

        current_client_id = (
            str(current_client_id).strip()
        )

        visitor_count = (
            await visitors_collection.count_documents(
                {
                    "client_id":
                        current_client_id
                }
            )
        )

        conversation_records = (
            await conversations_collection.find(
                {
                    "client_id":
                        current_client_id
                },
                {
                    "_id": 0,
                    "messages": 1,
                },
            ).to_list(
                length=None
            )
        )

        conversation_count = len(
            conversation_records
        )

        message_count = (
            _message_count_from_conversations(
                conversation_records
            )
        )

        result.append(
            {
                "client_id":
                    current_client_id,

                "name":
                    client.get(
                        "business_name"
                    )
                    or current_client_id,

                "visitors":
                    visitor_count,

                "conversations":
                    conversation_count,

                "messages":
                    message_count,

                "status":
                    "Active",
            }
        )

    return result