from __future__ import annotations

"""
Background worker: candidate scoring.

Computes a deterministic fit score for a candidate against their role's
requirements and persists the result as a ``CandidateScore`` record.

Pipeline:
  1. Load the ``Candidate`` and its associated ``Role``.
  2. Assert that ``structured_json`` and ``requirements_json`` are available.
  3. Call the scoring service to produce a ``ScoringResult``.
  4. Upsert a ``CandidateScore`` record.
  5. Update ``Candidate.status`` to ``scored``.

In production, run this as a separate process consuming from an Azure
Service Bus queue.

TODO: Add semantic similarity re-ranking using the pgvector retrieval service.
"""

import logging
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore
from app.models.role import Role
from app.services import scoring as scoring_service

logger = logging.getLogger(__name__)


async def enqueue_score_candidate(candidate_id: str) -> None:
    """
    Entry point for kicking off candidate scoring.

    Args:
        candidate_id: String UUID of the ``Candidate`` to score.
    """
    logger.info("Enqueuing score job for candidate %s", candidate_id)
    await run_score_candidate(candidate_id)


async def run_score_candidate(candidate_id: str) -> None:
    """
    Core scoring logic executed by the background worker.

    Args:
        candidate_id: String UUID of the ``Candidate`` to score.

    TODO:
        - Implement real scoring once ``scoring_service`` factor methods are complete.
        - Add pgvector re-ranking pass using the candidate's embedding.
        - Emit a ``UsageEvent`` for billing / analytics.
    """
    logger.info("Starting score job for candidate %s", candidate_id)

    async with AsyncSessionLocal() as db:
        try:
            # ----------------------------------------------------------------
            # Load candidate and role
            # ----------------------------------------------------------------
            candidate = await db.get(Candidate, uuid.UUID(candidate_id))
            if candidate is None:
                logger.error("Candidate %s not found — aborting score job.", candidate_id)
                return

            role = await db.get(Role, candidate.role_id)
            if role is None:
                logger.error(
                    "Role %s not found for candidate %s — aborting.", candidate.role_id, candidate_id
                )
                return

            # ----------------------------------------------------------------
            # Guard: we need structured data and role requirements
            # ----------------------------------------------------------------
            structured = candidate.structured_json or {}
            requirements = role.requirements_json or {}

            if not structured:
                logger.warning(
                    "Candidate %s has no structured_json — scoring with empty data.", candidate_id
                )
            if not requirements:
                logger.warning(
                    "Role %s has no requirements_json — scoring with empty requirements.",
                    role.id,
                )

            # ----------------------------------------------------------------
            # Compute score
            # ----------------------------------------------------------------
            result = await scoring_service.score_candidate(structured, requirements)

            # ----------------------------------------------------------------
            # Upsert CandidateScore
            # ----------------------------------------------------------------
            existing = await db.execute(
                select(CandidateScore).where(
                    CandidateScore.candidate_id == candidate.id,
                    CandidateScore.role_id == role.id,
                )
            )
            score_record = existing.scalar_one_or_none()

            if score_record is None:
                score_record = CandidateScore(
                    candidate_id=candidate.id,
                    role_id=role.id,
                )
                db.add(score_record)

            score_record.overall_score = result.overall_score
            score_record.factor_scores_json = result.factor_scores
            score_record.reasons_json = result.reasons
            score_record.strengths = result.strengths
            score_record.risks = result.risks
            score_record.missing_evidence = result.missing_evidence

            candidate.status = "scored"
            await db.commit()

            logger.info(
                "Scoring complete for candidate %s — overall=%.1f",
                candidate_id,
                result.overall_score,
            )

        except Exception:
            logger.exception("Score job failed for candidate %s", candidate_id)
            raise
