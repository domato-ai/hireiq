from __future__ import annotations

"""
Embedding generation service.

Converts text into dense vector representations for semantic similarity
search powered by pgvector.

Target model: ``text-embedding-ada-002`` (1536 dims) via Azure OpenAI.

TODO:
  - Configure Azure OpenAI endpoint and deployment in settings.
  - Implement ``generate`` using the ``openai`` async client.
  - Add retry logic (tenacity) for transient API failures.
  - Cache embeddings keyed by content hash to avoid re-embedding.
"""

import hashlib
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536
EMBEDDING_MODEL = "text-embedding-ada-002"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def generate(text: str) -> list[float]:
    """
    Generate a 1536-dimensional embedding vector for the given text.

    Args:
        text: Plain text to embed (e.g. a resume chunk or job description).

    Returns:
        A list of 1536 floats representing the embedding.

    Raises:
        EmbeddingError: If the embedding API call fails after retries.
    """
    from app.services.llm import embed

    results = await embed([text])
    return results[0]


async def generate_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.

    Batching reduces API round-trips. Azure OpenAI supports up to 16 items
    per chunk to stay within safe request limits.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors in the same order as the input.
    """
    from app.services.llm import embed

    # Azure OpenAI has a batch limit; process in chunks of 16
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), 16):
        batch = texts[i : i + 16]
        results = await embed(batch)
        all_embeddings.extend(results)
    return all_embeddings


def content_hash(text: str) -> str:
    """Return a stable SHA-256 hex digest for deduplication / caching."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingError(Exception):
    """Raised when embedding generation fails after retries."""
