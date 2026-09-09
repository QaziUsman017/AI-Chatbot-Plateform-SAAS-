"""
Client-specific retrieval logic for RAG.

Retrieves knowledge-base chunks from Qdrant using a strict
client_id filter so that each client's knowledge remains isolated.
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

    Uses Qdrant's search endpoint and strictly filters results
    by client_id.

    This function is intentionally synchronous because the
    QdrantClient and embedding function are synchronous.
    """

    # =========================================================
    # VALIDATE QUERY
    # =========================================================

    if not query or not str(query).strip():
        print("RAG: Empty query.")
        return []

    query = str(query).strip()

    # =========================================================
    # NORMALIZE LIMIT
    # =========================================================

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        print(
            f"RAG: Invalid limit received: {repr(limit)}. "
            "Using default limit=5."
        )
        limit = 5

    if limit <= 0:
        print(
            f"RAG: Invalid limit={limit}. "
            "Using default limit=5."
        )
        limit = 5

    # Prevent unnecessarily large retrieval requests.
    limit = min(limit, 20)

    # =========================================================
    # NORMALIZE CLIENT ID
    # =========================================================

    client_id = str(client_id or "").strip()

    if not client_id:
        print("RAG: Missing client_id.")
        return []

    # =========================================================
    # ENSURE COLLECTION EXISTS
    # =========================================================

    try:
        create_collection()

    except Exception as exc:
        print("========================================")
        print("RAG COLLECTION ERROR")
        print(type(exc).__name__)
        print(repr(exc))
        print("========================================")
        return []

    # =========================================================
    # GENERATE QUERY EMBEDDING
    # =========================================================

    try:
        query_embedding = generate_embedding(query)

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

    # =========================================================
    # VALIDATE EMBEDDING DIMENSION
    # =========================================================

    embedding_dimension = len(query_embedding)

    if embedding_dimension != 384:
        print("========================================")
        print("RAG EMBEDDING DIMENSION ERROR")
        print(
            f"Expected: 384 | Received: {embedding_dimension}"
        )
        print("========================================")
        return []

    # =========================================================
    # RETRIEVAL LOG
    # =========================================================

    print("========================================")
    print("RAG RETRIEVAL")
    print("========================================")
    print("QUERY:")
    print(repr(query))
    print("CLIENT ID:")
    print(repr(client_id))
    print("LIMIT:")
    print(limit)
    print("EMBEDDING DIMENSION:")
    print(embedding_dimension)
    print("COLLECTION:")
    print(COLLECTION_NAME)
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
        print("RAG: Sending search request to Qdrant...")

        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=client_filter,
            limit=limit,
            with_payload=True,
        )

        results = search_result or []

        print("RAG: Qdrant search request completed.")

    except Exception as exc:
        print("========================================")
        print("QDRANT RETRIEVAL ERROR")
        print("========================================")
        print("TYPE:")
        print(type(exc).__name__)
        print("ERROR:")
        print(repr(exc))

        # Some Qdrant exceptions expose the raw server response.
        if hasattr(exc, "content"):
            try:
                print("QDRANT RESPONSE CONTENT:")
                print(exc.content)
            except Exception:
                pass

        if hasattr(exc, "status_code"):
            try:
                print("QDRANT STATUS CODE:")
                print(exc.status_code)
            except Exception:
                pass

        print("========================================")

        return []

    # =========================================================
    # RESULTS COUNT
    # =========================================================

    print("========================================")
    print("QDRANT RESULTS COUNT:")
    print(len(results))
    print("========================================")

    # =========================================================
    # PROCESS RESULTS
    # =========================================================

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

        score = getattr(
            result,
            "score",
            None,
        )

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
        # IGNORE EMPTY TEXT
        # =====================================================

        if not text:
            print(
                "RAG: Skipping result because text is empty."
            )
            continue

        # =====================================================
        # EXTRA CLIENT ISOLATION
        # =====================================================

        if result_client_id != client_id:
            print(
                "RAG: Skipping result because client_id "
                "does not match authenticated client."
            )
            continue

        # =====================================================
        # STORE VALID RESULT
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