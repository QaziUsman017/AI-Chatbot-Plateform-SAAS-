"""Vector database integration using Qdrant Cloud."""

from __future__ import annotations

import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)


COLLECTION_NAME = "chatbot_documents"
VECTOR_SIZE = 384


# Qdrant Cloud configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


if not QDRANT_URL:
    raise RuntimeError(
        "QDRANT_URL environment variable is not set."
    )


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def create_collection() -> None:
    """
    Create the document collection if it does not already exist.

    Also ensures that the client_id payload field has a
    keyword index, which is required for client-specific
    Qdrant filtering.
    """

    collections = client.get_collections().collections

    existing_names = {
        collection.name
        for collection in collections
    }

    # Create collection if it does not exist.
    if COLLECTION_NAME not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

    # Ensure client_id has a keyword payload index.
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="client_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )

        print(
            "QDRANT: client_id payload index created/ensured."
        )

    except Exception as exc:
        error_text = str(exc).lower()

        # Qdrant may report that the index already exists.
        # That is safe and should not stop the application.
        if (
            "already exists" in error_text
            or "index already exists" in error_text
        ):
            print(
                "QDRANT: client_id payload index already exists."
            )
        else:
            print(
                "QDRANT: Failed to create client_id payload index."
            )
            print(
                f"QDRANT INDEX ERROR: {exc}"
            )


def collection_exists() -> bool:
    """Check whether the chatbot document collection exists."""

    collections = client.get_collections().collections

    return COLLECTION_NAME in {
        collection.name
        for collection in collections
    }