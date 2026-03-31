from __future__ import annotations

"""
Semantic retrieval service powered by pgvector.

Uses cosine similarity between candidate embeddings and a query vector
(typically derived from the role's job description) to return the most
relevant candidates for a given role.

Prerequisites:
  - The ``pgvector`` PostgreSQL extension must be installed.
  - Candidates must have their ``embedding`` column populated.
  - An HNSW or IVFFlat index should be created on ``candidates.embedding``
    for efficient ANN search at scale:

      CREATE INDEX ON candidates USING hnsw (embedding vector_cosine_ops);

TODO: Implement full retrieval once embeddings are live.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import generate

logger = logging.getLogger(__name__)

# Default number of top candidates to return
DEFAULT_TOP_K = 20


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def retrieve_top_candidates(
    role_id,
    query_embedding: list[float],
    db: AsyncSession,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """Retrieve top K candidates by cosine similarity to the query embedding."""
    sql = text("""
        SELECT id, name,
               1 - (embedding <=> :vec::vector) AS similarity
        FROM candidates
        WHERE role_id = :role_id
          AND embedding IS NOT NULL
          AND status = 'scored'
        ORDER BY embedding <=> :vec::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "role_id": str(role_id),
        "vec": str(query_embedding),
        "top_k": top_k,
    })

    return [{"id": row.id, "name": row.name, "similarity": row.similarity} for row in result]


async def retrieve_similar_candidates(
    candidate_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Find candidates similar to a given candidate within the same role.

    Useful for the "find similar" feature in the comparison view.

    Args:
        candidate_id: Reference candidate whose embedding is used as the query.
        role_id: Scope search to this role's candidate pool.
        db: Async database session.
        top_k: Number of similar candidates to return.

    Returns:
        List of dicts with ``candidate_id`` and ``similarity`` keys,
        excluding the reference candidate itself.

    TODO: Implement once embeddings are populated.
    """
    logger.warning(
        "Similar candidate retrieval is not yet implemented — returning empty list."
    )
    return []
