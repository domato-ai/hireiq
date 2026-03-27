from __future__ import annotations

"""
Background worker: embedding generation.

Converts a candidate's extracted resume text into a dense vector and stores
it in ``Candidate.embedding`` for pgvector-powered semantic search.

Pipeline:
  1. Receive ``candidate_id`` and ``raw_text``.
  2. Chunk the text into overlapping segments.
  3. Generate embeddings for each chunk via the embeddings service.
  4. Average the chunk embeddings into a single document vector.
  5. Persist the vector to ``Candidate.embedding``.
  6. Update status to ``embedded``.
  7. Enqueue the scoring worker.

In production, run this as a separate process consuming from an Azure
Service Bus queue.

TODO: Replace the module-level direct-call pattern with a proper queue consumer.
"""

import logging
import uuid

from app.database import AsyncSessionLocal
from app.models.candidate import Candidate
from app.services import embeddings as embedding_service
from app.services import parser as parser_service

logger = logging.getLogger(__name__)


async def enqueue_generate_embeddings(candidate_id: str, raw_text: str) -> None:
    """
    Entry point for kicking off embedding generation.

    Args:
        candidate_id: String UUID of the ``Candidate`` to embed.
        raw_text: Plain-text content extracted from the resume.
    """
    logger.info("Enqueuing embedding job for candidate %s", candidate_id)
    await run_generate_embeddings(candidate_id, raw_text)


async def run_generate_embeddings(candidate_id: str, raw_text: str) -> None:
    """
    Core embedding logic executed by the background worker.

    Args:
        candidate_id: String UUID of the ``Candidate`` to update.
        raw_text: Extracted plain text from the resume.

    TODO:
        - Chunk text with ``parser_service.chunk_text``.
        - Generate per-chunk embeddings with ``embedding_service.generate_batch``.
        - Average chunk vectors (mean pooling).
        - Persist to ``Candidate.embedding``.
        - Enqueue ``score_candidates`` worker.
    """
    logger.info("Starting embedding job for candidate %s", candidate_id)

    async with AsyncSessionLocal() as db:
        try:
            candidate = await db.get(Candidate, uuid.UUID(candidate_id))
            if candidate is None:
                logger.error("Candidate %s not found — aborting embedding job.", candidate_id)
                return

            if not raw_text.strip():
                logger.warning("Candidate %s has empty raw_text — skipping embedding.", candidate_id)
                return

            # ----------------------------------------------------------------
            # Chunk the text
            # ----------------------------------------------------------------
            chunks = await parser_service.chunk_text(raw_text)
            logger.debug("Candidate %s: %d text chunks", candidate_id, len(chunks))

            # ----------------------------------------------------------------
            # Generate per-chunk embeddings
            # ----------------------------------------------------------------
            chunk_vectors = await embedding_service.generate_batch(chunks)

            # ----------------------------------------------------------------
            # Mean-pool chunk vectors into a single document vector
            # ----------------------------------------------------------------
            dim = embedding_service.EMBEDDING_DIM
            if chunk_vectors:
                doc_vector = [
                    sum(vec[i] for vec in chunk_vectors) / len(chunk_vectors)
                    for i in range(dim)
                ]
            else:
                doc_vector = [0.0] * dim

            # ----------------------------------------------------------------
            # Persist
            # ----------------------------------------------------------------
            candidate.embedding = doc_vector  # type: ignore[assignment]
            await db.commit()

            logger.info("Embedding complete for candidate %s", candidate_id)

            # ----------------------------------------------------------------
            # Enqueue scoring
            # ----------------------------------------------------------------
            from app.workers.score_candidates import enqueue_score_candidate  # noqa: PLC0415

            await enqueue_score_candidate(candidate_id)

        except Exception:
            logger.exception("Embedding job failed for candidate %s", candidate_id)
            raise
