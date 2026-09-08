"""RAG service for client-specific document indexing."""

from __future__ import annotations

from uuid import uuid4

from qdrant_client.models import PointStruct

from backend.database.vector_db import (
    COLLECTION_NAME,
    client,
    create_collection,
)
from backend.services.rag.chunking import chunk_text
from backend.services.rag.embeddings import generate_embeddings


def index_text(
    text: str,
    source: str = "unknown",
    client_id: str = "",
) -> int:
    """Chunk text, generate embeddings, and store them for a specific client."""

    if not text or not text.strip():
        return 0

    client_id = client_id.strip()

    if not client_id:
        raise ValueError(
            "client_id is required for knowledge indexing."
        )

    create_collection()

    chunks = chunk_text(text)

    if not chunks:
        return 0

    embeddings = generate_embeddings(chunks)

    points: list[PointStruct] = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "text": chunk,
                    "source": source,
                    "client_id": client_id,
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)