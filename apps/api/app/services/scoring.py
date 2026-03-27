from __future__ import annotations

"""
Deterministic scoring engine.

Scores a candidate against a role's requirements without relying on an LLM.
The algorithm uses weighted factor matching on structured resume fields.

Factors (configurable weights):
  - skills_match      (40 %): required skills present in candidate's skill list
  - experience_years  (25 %): years of relevant experience vs. requirement
  - education_match   (15 %): required education level vs. candidate's highest
  - title_proximity   (10 %): semantic closeness of previous titles to the role
  - location_match    (10 %): geography / remote preference alignment

TODO: Implement each factor. Placeholder returns a zero score.
"""

from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor weights (must sum to 1.0)
# ---------------------------------------------------------------------------

FACTOR_WEIGHTS: dict[str, float] = {
    "skills_match": 0.40,
    "experience_years": 0.25,
    "education_match": 0.15,
    "title_proximity": 0.10,
    "location_match": 0.10,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ScoringResult:
    overall_score: float                          # 0.0 – 100.0
    factor_scores: dict[str, float] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def score_candidate(
    candidate_structured: dict[str, Any],
    role_requirements: dict[str, Any],
) -> ScoringResult:
    """
    Compute a deterministic fit score for a candidate against a role.

    Args:
        candidate_structured: Parsed resume fields from ``Candidate.structured_json``.
        role_requirements: Structured requirements from ``Role.requirements_json``.

    Returns:
        A ``ScoringResult`` with per-factor breakdown and narrative signals.
    """
    factor_scores: dict[str, float] = {}
    reasons: dict[str, str] = {}

    factor_scores["skills_match"] = await _score_skills(
        candidate_structured, role_requirements, reasons
    )
    factor_scores["experience_years"] = await _score_experience(
        candidate_structured, role_requirements, reasons
    )
    factor_scores["education_match"] = await _score_education(
        candidate_structured, role_requirements, reasons
    )
    factor_scores["title_proximity"] = await _score_title(
        candidate_structured, role_requirements, reasons
    )
    factor_scores["location_match"] = await _score_location(
        candidate_structured, role_requirements, reasons
    )

    overall = sum(
        factor_scores.get(factor, 0.0) * weight
        for factor, weight in FACTOR_WEIGHTS.items()
    )

    strengths, risks, missing = _extract_signals(factor_scores, candidate_structured, role_requirements)

    result = ScoringResult(
        overall_score=round(overall, 2),
        factor_scores=factor_scores,
        reasons=reasons,
        strengths=strengths,
        risks=risks,
        missing_evidence=missing,
    )

    logger.info(
        "Scored candidate: overall=%.1f skills=%.1f exp=%.1f",
        result.overall_score,
        factor_scores.get("skills_match", 0),
        factor_scores.get("experience_years", 0),
    )
    return result


# ---------------------------------------------------------------------------
# Factor scorers (stubs)
# ---------------------------------------------------------------------------


async def _score_skills(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Compute skills match score (0–100).

    TODO:
      - Extract ``required_skills`` from requirements and ``skills`` from candidate.
      - Count exact and fuzzy matches.
      - Score = (matched / total_required) * 100, capped at 100.
    """
    reasons["skills_match"] = "Skill matching not yet implemented."
    return 0.0


async def _score_experience(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score years of relevant experience (0–100).

    TODO:
      - Extract ``min_years_experience`` from requirements.
      - Sum years from candidate's work history.
      - Apply diminishing returns above the minimum.
    """
    reasons["experience_years"] = "Experience scoring not yet implemented."
    return 0.0


async def _score_education(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score education level match (0–100).

    TODO:
      - Map degree names to numeric levels: high_school=1, bachelor=2,
        master=3, phd=4.
      - Score = 100 if candidate_level >= required_level, else proportional.
    """
    reasons["education_match"] = "Education scoring not yet implemented."
    return 0.0


async def _score_title(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score title proximity (0–100).

    TODO:
      - Compare most recent job titles to role title using token overlap.
      - Consider using cosine similarity on pre-computed embeddings.
    """
    reasons["title_proximity"] = "Title proximity scoring not yet implemented."
    return 0.0


async def _score_location(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score location / remote alignment (0–100).

    TODO:
      - Check if role is remote-friendly.
      - Compare candidate's stated location / work preference.
    """
    reasons["location_match"] = "Location scoring not yet implemented."
    return 0.0


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------


def _extract_signals(
    factor_scores: dict[str, float],
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    """
    Derive human-readable strengths, risks, and missing evidence from scores.

    TODO: Implement rule-based signal extraction per factor.
    """
    strengths: list[str] = []
    risks: list[str] = []
    missing: list[str] = []
    return strengths, risks, missing
