"""
Embedding utilities for RAG.

Uses Hugging Face Inference API so the heavy
Sentence Transformers / PyTorch stack is NOT bundled
inside the Vercel serverless function.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

HF_API_URL = (
    "https://router.huggingface.co/"
    "hf-inference/models/"
    f"{MODEL_NAME}/pipeline/feature-extraction"
)

HF_API_KEY = os.getenv("Token")

VECTOR_SIZE = 384

REQUEST_TIMEOUT = 60.0


# =========================================================
# VALIDATION
# =========================================================

def _validate_api_key() -> None:
    """Ensure the Hugging Face API key exists."""

    if not HF_API_KEY:
        raise RuntimeError(
            "HF_API_KEY environment variable is not set."
        )


# =========================================================
# RESPONSE NORMALIZATION
# =========================================================

def _extract_embedding(
    response_data: Any,
) -> list[float]:
    """
    Convert Hugging Face feature-extraction response
    into a single 384-dimensional sentence embedding.

    Hugging Face may return:

        [384]

    or:

        [[token_vectors], ...]

    For token-level output, mean pooling is applied.
    """

    data = response_data

    # -----------------------------------------------------
    # Case 1:
    # Direct vector: [384]
    # -----------------------------------------------------

    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], (int, float))
    ):
        embedding = [
            float(value)
            for value in data
        ]

        if len(embedding) != VECTOR_SIZE:
            raise RuntimeError(
                "Unexpected embedding dimension: "
                f"{len(embedding)}. "
                f"Expected {VECTOR_SIZE}."
            )

        return _normalize_embedding(embedding)

    # -----------------------------------------------------
    # Case 2:
    # Batch with one vector: [[384]]
    # -----------------------------------------------------

    if (
        isinstance(data, list)
        and len(data) == 1
        and isinstance(data[0], list)
        and data[0]
        and isinstance(data[0][0], (int, float))
    ):
        embedding = [
            float(value)
            for value in data[0]
        ]

        if len(embedding) != VECTOR_SIZE:
            raise RuntimeError(
                "Unexpected embedding dimension: "
                f"{len(embedding)}. "
                f"Expected {VECTOR_SIZE}."
            )

        return _normalize_embedding(embedding)

    # -----------------------------------------------------
    # Case 3:
    # Token embeddings:
    #
    # [
    #   [token1...],
    #   [token2...],
    #   ...
    # ]
    # -----------------------------------------------------

    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], list)
    ):
        token_vectors = data

        valid_vectors: list[list[float]] = []

        for vector in token_vectors:

            if not isinstance(vector, list):
                continue

            if len(vector) != VECTOR_SIZE:
                continue

            if not all(
                isinstance(value, (int, float))
                for value in vector
            ):
                continue

            valid_vectors.append(
                [float(value) for value in vector]
            )

        if not valid_vectors:
            raise RuntimeError(
                "Hugging Face returned an unexpected "
                "embedding format."
            )

        # -------------------------------------------------
        # Mean pooling
        # -------------------------------------------------

        embedding = []

        for dimension in range(VECTOR_SIZE):

            value = sum(
                vector[dimension]
                for vector in valid_vectors
            )

            value /= len(valid_vectors)

            embedding.append(value)

        return _normalize_embedding(embedding)

    raise RuntimeError(
        "Unable to extract embedding from "
        "Hugging Face response."
    )


# =========================================================
# NORMALIZATION
# =========================================================

def _normalize_embedding(
    embedding: list[float],
) -> list[float]:
    """
    L2-normalize an embedding.

    This matches the previous
    normalize_embeddings=True behavior.
    """

    magnitude_squared = sum(
        value * value
        for value in embedding
    )

    magnitude = magnitude_squared ** 0.5

    if magnitude == 0:
        return embedding

    return [
        value / magnitude
        for value in embedding
    ]


# =========================================================
# API REQUEST
# =========================================================

async def _generate_embedding_async(
    text: str,
) -> list[float]:
    """Generate one embedding asynchronously."""

    _validate_api_key()

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": text,
    }

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT
    ) as http_client:

        response = await http_client.post(
            HF_API_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code != 200:

        raise RuntimeError(
            "Hugging Face embedding API failed. "
            f"Status: {response.status_code}. "
            f"Response: {response.text[:1000]}"
        )

    try:
        response_data = response.json()

    except Exception as exc:

        raise RuntimeError(
            "Hugging Face returned invalid JSON."
        ) from exc

    return _extract_embedding(response_data)


# =========================================================
# PUBLIC API
# =========================================================

def generate_embedding(
    text: str,
) -> list[float]:
    """
    Generate an embedding vector for a single text.

    This function remains synchronous so existing RAG
    code does not need to change.
    """

    if not text or not text.strip():
        return []

    # -----------------------------------------------------
    # Run async HTTP request from synchronous code.
    # -----------------------------------------------------

    import asyncio

    try:
        asyncio.get_running_loop()

    except RuntimeError:

        return asyncio.run(
            _generate_embedding_async(
                text.strip()
            )
        )

    # -----------------------------------------------------
    # If an event loop is already running, use a separate
    # thread to safely execute the async request.
    # -----------------------------------------------------

    import threading

    result: list[float] = []
    error: list[Exception] = []

    def runner() -> None:

        try:
            result.extend(
                asyncio.run(
                    _generate_embedding_async(
                        text.strip()
                    )
                )
            )

        except Exception as exc:
            error.append(exc)

    thread = threading.Thread(
        target=runner
    )

    thread.start()
    thread.join()

    if error:
        raise error[0]

    return result


def generate_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.

    Uses the same Hugging Face model and keeps the
    existing 384-dimensional vector format.
    """

    if not texts:
        return []

    embeddings: list[list[float]] = []

    for text in texts:

        if not text or not text.strip():
            embeddings.append([])
            continue

        embeddings.append(
            generate_embedding(
                text.strip()
            )
        )

    return embeddings