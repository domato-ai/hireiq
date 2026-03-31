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

    Must-have skills are weighted 2x relative to nice-to-have skills.
    Matching is case-insensitive token overlap.
    """
    candidate_skills: list[str] = [s.lower().strip() for s in (candidate.get("skills") or []) if s]

    must_have: list[str] = [s.lower().strip() for s in (requirements.get("must_have_skills") or []) if s]
    nice_to_have: list[str] = [s.lower().strip() for s in (requirements.get("nice_to_have_skills") or []) if s]

    if not must_have and not nice_to_have:
        reasons["skills_match"] = "No skill requirements specified; score defaulted to 100."
        return 100.0

    def _token_match(req_skill: str, candidate_skills: list[str]) -> bool:
        req_tokens = set(req_skill.split())
        for cs in candidate_skills:
            cs_tokens = set(cs.split())
            if req_tokens & cs_tokens:
                return True
        return False

    must_matched = sum(1 for s in must_have if _token_match(s, candidate_skills))
    nice_matched = sum(1 for s in nice_to_have if _token_match(s, candidate_skills))

    # Weighted numerator: must-have worth 2 points each, nice-to-have worth 1 point each
    max_points = len(must_have) * 2 + len(nice_to_have) * 1
    earned_points = must_matched * 2 + nice_matched * 1

    score = (earned_points / max_points) * 100.0 if max_points > 0 else 100.0

    missing_must = [s for s in must_have if not _token_match(s, candidate_skills)]
    reasons["skills_match"] = (
        f"Matched {must_matched}/{len(must_have)} must-have and "
        f"{nice_matched}/{len(nice_to_have)} nice-to-have skills. "
        + (f"Missing must-have: {', '.join(missing_must)}." if missing_must else "All must-have skills present.")
    )
    return round(score, 2)


async def _score_experience(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score years of relevant experience (0–100).

    At or above required years = 100. Within 1 year under = 75.
    Within 2 years under = 50. Further under = scaled proportionally.
    """
    required_raw = requirements.get("years_experience")
    candidate_raw = candidate.get("years_experience")

    if required_raw is None:
        reasons["experience_years"] = "No experience requirement specified; score defaulted to 100."
        return 100.0

    if candidate_raw is None:
        reasons["experience_years"] = "Candidate years of experience not available."
        return 0.0

    try:
        required = float(required_raw)
        actual = float(candidate_raw)
    except (TypeError, ValueError):
        reasons["experience_years"] = "Could not parse years of experience as numbers."
        return 0.0

    gap = required - actual

    if gap <= 0:
        score = 100.0
        reasons["experience_years"] = (
            f"Candidate has {actual:.1f} years; requirement is {required:.1f}. Meets or exceeds requirement."
        )
    elif gap <= 1:
        score = 75.0
        reasons["experience_years"] = (
            f"Candidate has {actual:.1f} years; requirement is {required:.1f}. Within 1 year of requirement."
        )
    elif gap <= 2:
        score = 50.0
        reasons["experience_years"] = (
            f"Candidate has {actual:.1f} years; requirement is {required:.1f}. Within 2 years of requirement."
        )
    else:
        # Scale down proportionally: 0 years experience against any requirement → 0
        score = max(0.0, (actual / required) * 50.0) if required > 0 else 0.0
        reasons["experience_years"] = (
            f"Candidate has {actual:.1f} years; requirement is {required:.1f}. "
            f"Significantly below requirement (gap: {gap:.1f} years)."
        )

    return round(score, 2)


async def _score_education(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score education level match (0–100).

    Degree hierarchy: associate=1, bachelor=2, master=3, phd=4.
    Score = 100 if candidate_level >= required_level, else proportional.
    """
    DEGREE_LEVELS: dict[str, int] = {
        "associate": 1,
        "associates": 1,
        "bachelor": 2,
        "bachelors": 2,
        "undergraduate": 2,
        "bs": 2,
        "ba": 2,
        "b.s.": 2,
        "b.a.": 2,
        "master": 3,
        "masters": 3,
        "ms": 3,
        "ma": 3,
        "m.s.": 3,
        "m.a.": 3,
        "mba": 3,
        "phd": 4,
        "ph.d.": 4,
        "doctorate": 4,
        "doctoral": 4,
    }

    def _detect_level(text: str) -> int | None:
        """Return the highest degree level found in the text, or None."""
        text_lower = text.lower()
        best = None
        for keyword, level in DEGREE_LEVELS.items():
            if keyword in text_lower:
                if best is None or level > best:
                    best = level
        return best

    education_req_raw = requirements.get("education_requirements") or ""
    education_candidate_raw = ""

    # Support both a plain string and a list of education entries
    edu_entries = candidate.get("education") or []
    if isinstance(edu_entries, str):
        education_candidate_raw = edu_entries
    elif isinstance(edu_entries, list):
        education_candidate_raw = " ".join(
            " ".join(str(v) for v in (e.values() if isinstance(e, dict) else [e]))
            for e in edu_entries
        )

    if not education_req_raw:
        reasons["education_match"] = "No education requirement specified; score defaulted to 100."
        return 100.0

    if not education_candidate_raw.strip():
        reasons["education_match"] = "Candidate education information not available."
        return 0.0

    required_level = _detect_level(str(education_req_raw))
    candidate_level = _detect_level(education_candidate_raw)

    if required_level is None:
        reasons["education_match"] = (
            f"Could not parse required education level from: '{education_req_raw}'. Score defaulted to 100."
        )
        return 100.0

    if candidate_level is None:
        reasons["education_match"] = (
            f"Could not determine candidate's degree level. Required: '{education_req_raw}'."
        )
        return 0.0

    level_labels = {1: "Associate", 2: "Bachelor's", 3: "Master's", 4: "PhD"}

    if candidate_level >= required_level:
        score = 100.0
        reasons["education_match"] = (
            f"Candidate holds {level_labels.get(candidate_level, candidate_level)} degree; "
            f"requirement is {level_labels.get(required_level, required_level)}. Meets requirement."
        )
    else:
        score = round((candidate_level / required_level) * 100.0, 2)
        reasons["education_match"] = (
            f"Candidate holds {level_labels.get(candidate_level, candidate_level)} degree; "
            f"requirement is {level_labels.get(required_level, required_level)}. Below required level."
        )

    return score


async def _score_title(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score title proximity (0–100) using keyword token overlap.

    Compares the candidate's current_title against the role title and
    seniority_level. Stopwords (e.g. "and", "of", "the") are excluded.
    """
    STOPWORDS = {"and", "of", "the", "a", "an", "in", "at", "for", "to", "with", "on"}

    SENIORITY_KEYWORDS: dict[str, set[str]] = {
        "junior": {"junior", "associate", "entry", "jr"},
        "mid": {"mid", "intermediate", "ii", "2"},
        "senior": {"senior", "sr", "lead", "principal", "staff"},
        "manager": {"manager", "management", "head", "director", "vp", "vice president"},
        "executive": {"executive", "cto", "ceo", "coo", "chief", "president"},
    }

    def _tokenize(text: str) -> set[str]:
        import re
        tokens = set(re.split(r"[\s\-/,]+", text.lower()))
        return tokens - STOPWORDS - {""}

    role_title: str = str(requirements.get("title") or "")
    seniority: str = str(requirements.get("seniority_level") or "")
    candidate_title: str = str(candidate.get("current_title") or "")

    if not role_title and not seniority:
        reasons["title_proximity"] = "No role title or seniority specified; score defaulted to 100."
        return 100.0

    if not candidate_title.strip():
        reasons["title_proximity"] = "Candidate current title not available."
        return 0.0

    role_tokens = _tokenize(role_title)
    # Also add tokens for seniority level
    if seniority:
        seniority_lower = seniority.lower().strip()
        for level, synonyms in SENIORITY_KEYWORDS.items():
            if seniority_lower in synonyms or seniority_lower == level:
                role_tokens |= synonyms
                break
        else:
            role_tokens |= _tokenize(seniority)

    candidate_tokens = _tokenize(candidate_title)

    if not role_tokens:
        reasons["title_proximity"] = "Could not extract meaningful tokens from role title."
        return 50.0

    overlap = role_tokens & candidate_tokens
    score = round((len(overlap) / len(role_tokens)) * 100.0, 2)
    score = min(score, 100.0)

    reasons["title_proximity"] = (
        f"Candidate title: '{candidate_title}'. Role: '{role_title}' (seniority: '{seniority}'). "
        f"Token overlap: {len(overlap)}/{len(role_tokens)} tokens matched."
    )
    return score


async def _score_location(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
    reasons: dict[str, str],
) -> float:
    """
    Score location / remote alignment (0–100).

    Rules:
    - If role remote_policy is "remote", any candidate matches (100).
    - Same city = 100, same country = 75, otherwise = 50.
    - If either location is missing, default to 50 (unknown).
    """
    remote_policy: str = str(requirements.get("remote_policy") or "").lower().strip()
    candidate_location: str = str(candidate.get("location") or "").lower().strip()
    role_location: str = str(requirements.get("location") or "").lower().strip()

    # Fully remote role: everyone qualifies
    if remote_policy in {"remote", "fully remote", "fully-remote", "100% remote"}:
        reasons["location_match"] = "Role is fully remote; all locations match."
        return 100.0

    # Candidate prefers/is remote
    if candidate_location in {"remote", "anywhere", "flexible"}:
        if remote_policy in {"hybrid", "flexible"}:
            reasons["location_match"] = (
                "Candidate is remote-flexible and role supports hybrid/flexible work."
            )
            return 85.0
        reasons["location_match"] = (
            f"Candidate is remote-flexible but role policy is '{remote_policy or 'on-site'}'."
        )
        return 50.0

    if not candidate_location or not role_location:
        reasons["location_match"] = (
            "Location information incomplete; defaulting to neutral score."
        )
        return 50.0

    # Compare tokens for city/country matching
    candidate_tokens = set(candidate_location.replace(",", " ").split())
    role_tokens = set(role_location.replace(",", " ").split())
    common = candidate_tokens & role_tokens

    if len(common) >= 2 or candidate_location == role_location:
        score = 100.0
        reasons["location_match"] = (
            f"Candidate location '{candidate_location}' closely matches role location '{role_location}'."
        )
    elif len(common) == 1:
        score = 75.0
        reasons["location_match"] = (
            f"Candidate location '{candidate_location}' partially matches role location '{role_location}' "
            f"(shared token: '{next(iter(common))}')."
        )
    else:
        score = 50.0
        reasons["location_match"] = (
            f"Candidate location '{candidate_location}' does not match role location '{role_location}'."
        )

    return round(score, 2)


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

    Strengths: factors scoring > 75.
    Risks: factors scoring < 50.
    Missing: factors where the underlying candidate data was null/empty.
    """
    FACTOR_LABELS: dict[str, str] = {
        "skills_match": "Skills alignment",
        "experience_years": "Years of experience",
        "education_match": "Education level",
        "title_proximity": "Title relevance",
        "location_match": "Location / remote alignment",
    }

    # Fields whose absence indicates missing evidence, keyed by factor name
    CANDIDATE_FIELDS: dict[str, str] = {
        "skills_match": "skills",
        "experience_years": "years_experience",
        "education_match": "education",
        "title_proximity": "current_title",
        "location_match": "location",
    }

    strengths: list[str] = []
    risks: list[str] = []
    missing: list[str] = []

    for factor, score in factor_scores.items():
        label = FACTOR_LABELS.get(factor, factor)
        field = CANDIDATE_FIELDS.get(factor)

        # Check for missing candidate data
        if field is not None:
            value = candidate.get(field)
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append(f"{label}: no candidate data provided.")
                continue

        if score > 75:
            strengths.append(f"{label} (score: {score:.0f}/100).")
        elif score < 50:
            risks.append(f"{label} is below threshold (score: {score:.0f}/100).")

    return strengths, risks, missing
