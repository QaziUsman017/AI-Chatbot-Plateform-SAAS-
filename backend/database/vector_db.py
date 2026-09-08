"""Vector database integration using Qdrant Cloud."""

from __future__ import annotations

import os

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


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
    """Create the document collection if it does not already exist."""

    collections = client.get_collections().collections

    existing_names = {
        collection.name
        for collection in collections
    }

    if COLLECTION_NAME not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )


def collection_exists() -> bool:
    """Check whether the chatbot document collection exists."""

    collections = client.get_collections().collections

    return COLLECTION_NAME in {
        collection.name
        for collection in collections
    }