"""
Client-specific retrieval logic for RAG.
"""

from __future__ import annotations

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from backend.database.vector_db import (
    COLLECTION_NAME,
    client,
    create_collection,
)

from backend.services.rag.embeddings import generate_embedding


# =========================================================
# CLIENT-SPECIFIC RETRIEVAL
# =========================================================

def retrieve_chunks(
    query: str,
    limit: int = 5,
    client_id: str = "",
) -> list[dict]:
    """
    Retrieve relevant knowledge-base chunks for a specific client.

    Every retrieval is strictly filtered by client_id so that
    one client's knowledge base can never be returned to another
    client.

    This function is intentionally synchronous because both
    QdrantClient and generate_embedding() are synchronous.
    """

    # =========================================================
    # VALIDATION
    # =========================================================

    if not query or not query.strip():
        print("RAG: Empty query.")
        return []

    if limit <= 0:
        print("RAG: Invalid limit.")
        return []

    client_id = str(
        client_id or ""
    ).strip()

    if not client_id:
        print("RAG: Missing client_id.")
        return []

    query = query.strip()

    # =========================================================
    # ENSURE COLLECTION EXISTS
    # =========================================================

    try:

        create_collection()

    except Exception as exc:

        print("========================================")
        print("RAG COLLECTION ERROR")
        print(repr(exc))
        print("========================================")

        return []

    # =========================================================
    # GENERATE QUERY EMBEDDING
    # =========================================================

    try:

        query_embedding = generate_embedding(
            query
        )

    except Exception as exc:

        print("========================================")
        print("RAG EMBEDDING ERROR")
        print(type(exc).__name__)
        print(repr(exc))
        print("========================================")

        return []

    if not query_embedding:

        print(
            "RAG: Failed to generate query embedding."
        )

        return []

    print("========================================")
    print("RAG RETRIEVAL")
    print("========================================")
    print("QUERY:")
    print(repr(query))
    print("CLIENT ID:")
    print(repr(client_id))
    print("EMBEDDING DIMENSION:")
    print(len(query_embedding))
    print("========================================")

    # =========================================================
    # CLIENT-SPECIFIC FILTER
    # =========================================================

    client_filter = Filter(
        must=[
            FieldCondition(
                key="client_id",
                match=MatchValue(
                    value=client_id,
                ),
            )
        ]
    )

    # =========================================================
    # QDRANT SEARCH
    # =========================================================

    try:

        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=client_filter,
            limit=limit,
            with_payload=True,
        )

        results = search_result.points

    except Exception as exc:

        print("========================================")
        print("QDRANT RETRIEVAL ERROR")
        print(type(exc).__name__)
        print(repr(exc))
        print("========================================")

        return []

    # =========================================================
    # RESULTS
    # =========================================================

    print("========================================")
    print("QDRANT RESULTS COUNT:")
    print(len(results))
    print("========================================")

    chunks: list[dict] = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        payload = result.payload or {}

        text = str(
            payload.get(
                "text",
                "",
            )
        ).strip()

        source = str(
            payload.get(
                "source",
                "",
            )
        ).strip()

        result_client_id = str(
            payload.get(
                "client_id",
                "",
            )
        ).strip()

        score = result.score

        print("----------------------------------------")
        print(f"RESULT #{index}")
        print("SCORE:")
        print(score)
        print("SOURCE:")
        print(repr(source))
        print("PAYLOAD CLIENT ID:")
        print(repr(result_client_id))
        print("TEXT:")
        print(repr(text[:500]))
        print("----------------------------------------")

        # =====================================================
        # IGNORE EMPTY CHUNKS
        # =====================================================

        if not text:

            print(
                "RAG: Skipping empty text chunk."
            )

            continue

        # =====================================================
        # EXTRA CLIENT ISOLATION CHECK
        # =====================================================

        if result_client_id != client_id:

            print(
                "RAG: Skipping chunk because client_id "
                "does not match authenticated client."
            )

            continue

        # =====================================================
        # STORE VALID CHUNK
        # =====================================================

        chunks.append(
            {
                "text": text,
                "source": source,
                "client_id": result_client_id,
                "score": score,
            }
        )

    # =========================================================
    # FINAL RESULTS
    # =========================================================

    print("========================================")
    print("FINAL RETRIEVED CHUNKS:")
    print(f"COUNT: {len(chunks)}")

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        print(
            f"[{index}] "
            f"score={chunk.get('score')} "
            f"source={chunk.get('source')}"
        )

        print(
            chunk.get(
                "text",
                "",
            )[:500]
        )

    print("========================================")

    return chunks