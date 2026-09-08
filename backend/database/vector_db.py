"""Vector database integration using Qdrant."""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


COLLECTION_NAME = "chatbot_documents"
VECTOR_SIZE = 384


# Persistent local Qdrant database
QDRANT_PATH = Path("backend/data/qdrant")


QDRANT_PATH.mkdir(
    parents=True,
    exist_ok=True,
)


client = QdrantClient(
    path=str(QDRANT_PATH),
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