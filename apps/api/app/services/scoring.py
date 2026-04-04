from __future__ import annotations

"""
Deterministic scoring engine.

Scores a candidate against a role's requirements without relying on an LLM.
Uses weighted factor matching on structured resume fields across 8 factors.

Factors (weights sum to 1.0):
  - skills_match          (25 %): must-have and nice-to-have skill comparison
  - experience_years      (15 %): years of experience vs requirement
  - experience_relevance  (15 %): industry/domain relevance of prior roles
  - education_match       (10 %): education level and field match
  - title_seniority       (10 %): title/seniority alignment
  - leadership            (10 %): cross-functional, team management evidence
  - impact_evidence       (10 %): quantified achievements, metrics, outcomes
  - location_fit          ( 5 %): location/remote compatibility
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor weights (must sum to 1.0)
# ---------------------------------------------------------------------------

FACTOR_WEIGHTS: dict[str, float] = {
    "skills_match": 0.25,
    "experience_years": 0.15,
    "experience_relevance": 0.15,
    "education_match": 0.10,
    "title_seniority": 0.10,
    "leadership": 0.10,
    "impact_evidence": 0.10,
    "location_fit": 0.05,
}

FACTOR_LABELS: dict[str, str] = {
    "skills_match": "Skills Match",
    "experience_years": "Experience Years",
    "experience_relevance": "Experience Relevance",
    "education_match": "Education Match",
    "title_seniority": "Title & Seniority",
    "leadership": "Leadership",
    "impact_evidence": "Impact Evidence",
    "location_fit": "Location Fit",
}

# Common skill synonyms for fuzzy matching
SKILL_SYNONYMS: dict[str, set[str]] = {
    "javascript": {"js", "javascript", "ecmascript"},
    "typescript": {"ts", "typescript"},
    "python": {"python", "py"},
    "react": {"react", "reactjs", "react.js"},
    "node": {"node", "nodejs", "node.js"},
    "angular": {"angular", "angularjs", "angular.js"},
    "vue": {"vue", "vuejs", "vue.js"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "azure": {"azure", "microsoft azure"},
    "postgres": {"postgres", "postgresql", "psql"},
    "mongo": {"mongo", "mongodb"},
    "docker": {"docker", "containerization"},
    "kubernetes": {"kubernetes", "k8s"},
    "ci/cd": {"ci/cd", "cicd", "ci cd", "continuous integration", "continuous deployment"},
    "machine learning": {"machine learning", "ml"},
    "artificial intelligence": {"artificial intelligence", "ai"},
    "natural language processing": {"natural language processing", "nlp"},
    "product management": {"product management", "pm"},
    "project management": {"project management", "pmp"},
    "sql": {"sql", "structured query language"},
    "nosql": {"nosql", "no-sql"},
    "graphql": {"graphql", "gql"},
    "rest": {"rest", "restful", "rest api", "restful api"},
    "agile": {"agile", "scrum", "kanban"},
    "c#": {"c#", "csharp", "c sharp"},
    "c++": {"c++", "cpp"},
    "go": {"go", "golang"},
    "ruby": {"ruby", "rb"},
    "java": {"java"},
    "kotlin": {"kotlin"},
    "swift": {"swift"},
    "terraform": {"terraform", "tf"},
    "redis": {"redis"},
    "elasticsearch": {"elasticsearch", "elastic search", "es"},
    "kafka": {"kafka", "apache kafka"},
    "spark": {"spark", "apache spark", "pyspark"},
    "data factory": {"data factory", "azure data factory", "adf"},
    "databricks": {"databricks", "azure databricks"},
    "power bi": {"power bi", "powerbi"},
    "data modelling": {"data modelling", "data modeling", "dimensional modelling", "dimensional modeling", "kimball", "star schema", "snowflake schema"},
    "etl": {"etl", "elt", "extract transform load", "data pipelines", "data pipeline"},
    "ssis": {"ssis", "sql server integration services"},
    "ssrs": {"ssrs", "sql server reporting services"},
    "data warehouse": {"data warehouse", "dwh", "data warehousing", "edw", "enterprise data warehouse"},
    "microsoft fabric": {"microsoft fabric", "fabric"},
    "lakehouse": {"lakehouse", "data lakehouse", "lake house", "medallion architecture"},
    "devops": {"devops", "dev ops", "azure devops", "ci cd", "ci/cd pipelines"},
    "api": {"api", "apis", "rest api", "rest apis", "web api"},
    "data migration": {"data migration", "migration", "data migrations"},
    "data governance": {"data governance", "data quality", "data stewardship"},
    "t-sql": {"t-sql", "tsql", "transact-sql", "sql server"},
    ".net": {".net", "dotnet", "asp.net", "asp .net", "c#"},
    "azure functions": {"azure functions", "function apps", "serverless"},
    "data engineering": {"data engineering", "data engineer"},
    "stakeholder management": {"stakeholder management", "stakeholder engagement", "business stakeholders"},
}

# Build reverse lookup: normalized token -> canonical name
_SYNONYM_LOOKUP: dict[str, str] = {}
for canonical, synonyms in SKILL_SYNONYMS.items():
    for syn in synonyms:
        _SYNONYM_LOOKUP[syn] = canonical

# Seniority levels (ordered low to high)
SENIORITY_LEVELS: dict[str, int] = {
    "intern": 0,
    "entry": 1,
    "junior": 1,
    "associate": 2,
    "mid": 3,
    "intermediate": 3,
    "senior": 4,
    "sr": 4,
    "lead": 5,
    "principal": 5,
    "staff": 5,
    "manager": 6,
    "head": 6,
    "director": 7,
    "vp": 8,
    "vice president": 8,
    "svp": 9,
    "executive": 10,
    "c-level": 10,
    "chief": 10,
    "cto": 10,
    "ceo": 10,
    "coo": 10,
    "cfo": 10,
    "cpo": 10,
}

LEADERSHIP_KEYWORDS: list[str] = [
    "led team", "managed team", "managed a team", "team lead", "team leader",
    "cross-functional", "cross functional", "mentored", "mentoring",
    "direct reports", "reporting to me", "managed engineers",
    "managed developers", "managed designers", "managed analysts",
    "oversaw", "supervised", "built the team", "grew the team",
    "hiring manager", "recruited", "coached",
    "led the", "leading the", "leading a", "head of",
    "people manager", "player-coach", "player coach",
]

IMPACT_PATTERNS: list[re.Pattern] = [
    re.compile(r'\d+%', re.IGNORECASE),
    re.compile(r'\$[\d,.]+[kmb]?', re.IGNORECASE),
    re.compile(r'[\d,.]+\s*(users|customers|clients|accounts|subscribers)', re.IGNORECASE),
    re.compile(r'(increased|decreased|improved|reduced|grew|boosted|saved|generated|delivered|achieved|drove|accelerated)\s+\w+\s+by\b', re.IGNORECASE),
    re.compile(r'(revenue|arr|mrr|gmv|nps|csat|conversion|retention|churn|engagement|throughput|latency|uptime)', re.IGNORECASE),
    re.compile(r'\b\d+x\b', re.IGNORECASE),
    re.compile(r'(launched|shipped|released|deployed)\b', re.IGNORECASE),
]

SAAS_KEYWORDS: set[str] = {
    "saas", "b2b", "b2c", "enterprise", "smb", "self-serve",
    "subscription", "recurring revenue", "arr", "mrr",
    "platform", "api", "sdk", "cloud", "multi-tenant",
}

DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "fintech": {"fintech", "payments", "billing", "banking", "insurance", "lending", "credit", "debit", "financial", "finance", "trading", "wealth", "investment"},
    "healthcare": {"healthcare", "health", "medical", "clinical", "pharma", "biotech", "telemedicine", "ehr", "hipaa"},
    "ecommerce": {"ecommerce", "e-commerce", "retail", "marketplace", "shopping", "checkout", "cart", "commerce"},
    "edtech": {"edtech", "education", "learning", "lms", "courseware", "tutoring"},
    "adtech": {"adtech", "advertising", "programmatic", "dsp", "ssp", "ad tech"},
    "cybersecurity": {"cybersecurity", "security", "infosec", "soc", "siem", "threat", "vulnerability"},
    "devtools": {"devtools", "developer tools", "developer experience", "dx", "ide", "ci/cd"},
    "data": {"data", "analytics", "data science", "data engineering", "big data", "data warehouse", "etl"},
    "ai/ml": {"ai", "ml", "machine learning", "artificial intelligence", "deep learning", "nlp", "computer vision"},
    "logistics": {"logistics", "supply chain", "shipping", "fulfillment", "warehouse", "delivery"},
    "social": {"social media", "social network", "community", "content", "creator"},
    "gaming": {"gaming", "game", "esports", "game development"},
    "real estate": {"real estate", "proptech", "property", "housing", "mortgage"},
    "hr/people": {"hr", "human resources", "people ops", "recruiting", "talent", "workforce", "hris"},
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ScoringResult:
    overall_score: float                                          # 0.0 – 100.0
    factor_scores: dict[str, dict[str, Any]] = field(default_factory=dict)  # factor_name -> detailed dict
    strengths: list[str] = field(default_factory=list)            # evidence-based
    risks: list[str] = field(default_factory=list)                # evidence-based
    missing_evidence: list[str] = field(default_factory=list)
    summary: str = ""                                             # recruiter-friendly summary
    recommendation: str = ""                                      # strong_yes | yes | maybe | no


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
    factor_scores: dict[str, dict[str, Any]] = {}

    factor_scores["skills_match"] = await _score_skills(candidate_structured, role_requirements)
    factor_scores["experience_years"] = await _score_experience_years(candidate_structured, role_requirements)
    factor_scores["experience_relevance"] = await _score_experience_relevance(candidate_structured, role_requirements)
    factor_scores["education_match"] = await _score_education(candidate_structured, role_requirements)
    factor_scores["title_seniority"] = await _score_title_seniority(candidate_structured, role_requirements)
    factor_scores["leadership"] = await _score_leadership(candidate_structured, role_requirements)
    factor_scores["impact_evidence"] = await _score_impact(candidate_structured, role_requirements)
    factor_scores["location_fit"] = await _score_location(candidate_structured, role_requirements)

    overall = sum(
        factor_scores[factor]["score"] * FACTOR_WEIGHTS[factor]
        for factor in FACTOR_WEIGHTS
    )
    overall = round(overall, 2)

    strengths = _build_strengths(factor_scores, candidate_structured, role_requirements)
    risks = _build_risks(factor_scores, candidate_structured, role_requirements)
    missing = _build_missing_evidence(factor_scores, candidate_structured)
    summary = _build_summary(overall, factor_scores, candidate_structured, role_requirements)
    recommendation = _compute_recommendation(overall)

    result = ScoringResult(
        overall_score=overall,
        factor_scores=factor_scores,
        strengths=strengths,
        risks=risks,
        missing_evidence=missing,
        summary=summary,
        recommendation=recommendation,
    )

    logger.info(
        "Scored candidate: overall=%.1f skills=%.1f exp=%.1f rec=%s",
        result.overall_score,
        factor_scores["skills_match"]["score"],
        factor_scores["experience_years"]["score"],
        result.recommendation,
    )
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_skill(skill: str) -> str:
    """Normalize a skill string to its canonical form."""
    s = skill.lower().strip()
    return _SYNONYM_LOOKUP.get(s, s)


def _skills_match(req_skill: str, candidate_skills: list[str]) -> bool:
    """Check if a required skill matches any candidate skill, using synonyms and substring matching."""
    req_norm = _normalize_skill(req_skill)
    req_tokens = set(req_norm.split())

    for cs in candidate_skills:
        cs_norm = _normalize_skill(cs)
        # Exact canonical match
        if req_norm == cs_norm:
            return True
        # Substring containment (e.g. "data factory" in "azure data factory")
        if req_norm in cs_norm or cs_norm in req_norm:
            return True
        # Token overlap — required is subset of candidate or vice versa
        cs_tokens = set(cs_norm.split())
        if req_tokens and cs_tokens and req_tokens <= cs_tokens:
            return True
        if req_tokens and cs_tokens and cs_tokens <= req_tokens:
            return True
        # Partial: significant token overlap (for multi-word skills)
        if len(req_tokens) > 1 or len(cs_tokens) > 1:
            overlap = req_tokens & cs_tokens
            if overlap and len(overlap) >= max(1, min(len(req_tokens), len(cs_tokens)) - 1):
                return True

    return False


def _get_candidate_text_blob(candidate: dict[str, Any]) -> str:
    """Build a searchable text blob from all candidate fields."""
    parts: list[str] = []
    for key in ("current_title", "current_company", "location", "summary"):
        val = candidate.get(key)
        if val:
            parts.append(str(val))

    for exp in (candidate.get("experience") or []):
        if isinstance(exp, dict):
            for k in ("title", "company", "duration", "highlights"):
                v = exp.get(k)
                if isinstance(v, list):
                    parts.extend(str(x) for x in v)
                elif v:
                    parts.append(str(v))
        elif isinstance(exp, str):
            parts.append(exp)

    for skill in (candidate.get("skills") or []):
        parts.append(str(skill))

    for edu in (candidate.get("education") or []):
        if isinstance(edu, dict):
            parts.extend(str(v) for v in edu.values() if v)
        elif isinstance(edu, str):
            parts.append(edu)

    for ach in (candidate.get("achievements") or []):
        parts.append(str(ach))

    for le in (candidate.get("leadership_evidence") or []):
        parts.append(str(le))

    for ind in (candidate.get("industries") or []):
        parts.append(str(ind))

    return " ".join(parts).lower()


def _detect_seniority(title: str) -> int:
    """Detect seniority level from a title string. Returns numeric level."""
    title_lower = title.lower().strip()
    best = 3  # default to mid-level
    found = False
    for keyword, level in SENIORITY_LEVELS.items():
        if keyword in title_lower:
            if not found or level > best:
                best = level
                found = True
    return best


def _verdict(score: float) -> str:
    """Convert a 0-100 score to a verdict label."""
    if score >= 80:
        return "strong"
    elif score >= 55:
        return "partial"
    elif score >= 25:
        return "weak"
    return "missing"


def _compute_recommendation(overall: float) -> str:
    if overall >= 80:
        return "strong_yes"
    elif overall >= 65:
        return "yes"
    elif overall >= 50:
        return "maybe"
    return "no"


# ---------------------------------------------------------------------------
# Factor scorers
# ---------------------------------------------------------------------------


async def _score_skills(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score skills match using LLM-assisted matching for accuracy across all industries."""
    from app.services import llm

    raw_skills = list(candidate.get("skills") or [])
    raw_techs = list(candidate.get("technologies") or [])
    candidate_skills: list[str] = list({s.strip() for s in raw_skills + raw_techs if s and s.strip()})
    must_have: list[str] = [s.strip() for s in (requirements.get("must_have_skills") or []) if s]
    nice_to_have: list[str] = [s.strip() for s in (requirements.get("nice_to_have_skills") or []) if s]

    if not must_have and not nice_to_have:
        return {
            "score": 100.0, "label": "Skills Match", "weight": FACTOR_WEIGHTS["skills_match"],
            "verdict": "strong", "jd_required": "No skill requirements specified",
            "candidate_has": f"{len(candidate_skills)} skills listed",
            "reasoning": "No skill requirements specified in the JD.", "matched": [], "missing": [],
        }

    # Use LLM to do intelligent matching — handles synonyms, abbreviations, related tech
    try:
        match_result = await llm.extract_json(
            prompt=f"""JD requires these skills:
Must-have: {', '.join(must_have)}
Nice-to-have: {', '.join(nice_to_have)}

Candidate has these skills/technologies: {', '.join(candidate_skills)}

Also consider the candidate's experience descriptions:
{'; '.join(h for exp in (candidate.get('experience') or []) if isinstance(exp, dict) for h in (exp.get('highlights') or [])[:3])}""",
            system="""You are a skills matching expert. Compare the JD requirements against the candidate's skills.
A skill matches if the candidate has the SAME skill, an EQUIVALENT technology, or demonstrable experience with it.
For example: "PySpark" matches "Apache Spark", "Azure Data Factory" matches "ADF" or "data pipelines using Azure Data Factory", "CI/CD" matches "Azure DevOps pipelines".

Return JSON:
{
  "must_have_matched": ["skill1", "skill2"],
  "must_have_missing": ["skill3"],
  "nice_to_have_matched": ["skill4"],
  "nice_to_have_missing": ["skill5"],
  "reasoning": "2-3 sentence explanation of the skills alignment, noting key matches and gaps"
}
Be thorough — scan ALL candidate skills and experience for evidence of each required skill. Don't miss matches due to different terminology.""",
        )

        must_matched = match_result.get("must_have_matched", [])
        must_missing = match_result.get("must_have_missing", [])
        nice_matched = match_result.get("nice_to_have_matched", [])
        nice_missing = match_result.get("nice_to_have_missing", [])
        llm_reasoning = match_result.get("reasoning", "")

    except Exception as e:
        logger.warning("LLM skills matching failed, falling back to keyword: %s", e)
        # Fallback to keyword matching
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        must_matched = [s for s in must_have if _skills_match(s, candidate_skills_lower)]
        must_missing = [s for s in must_have if not _skills_match(s, candidate_skills_lower)]
        nice_matched = [s for s in nice_to_have if _skills_match(s, candidate_skills_lower)]
        nice_missing = [s for s in nice_to_have if not _skills_match(s, candidate_skills_lower)]
        llm_reasoning = ""

    # Deterministic scoring from the match results
    max_points = len(must_have) * 2 + len(nice_to_have) * 1
    earned_points = len(must_matched) * 2 + len(nice_matched) * 1
    score = (earned_points / max_points) * 100.0 if max_points > 0 else 100.0
    score = round(min(score, 100.0), 2)

    jd_required_parts = []
    if must_have:
        jd_required_parts.append(f"Must-have: {', '.join(must_have)}")
    if nice_to_have:
        jd_required_parts.append(f"Nice-to-have: {', '.join(nice_to_have)}")

    reasoning = llm_reasoning or f"Matched {len(must_matched)}/{len(must_have)} must-have and {len(nice_matched)}/{len(nice_to_have)} nice-to-have skills."

    return {
        "score": score,
        "label": "Skills Match",
        "weight": FACTOR_WEIGHTS["skills_match"],
        "verdict": _verdict(score),
        "jd_required": "; ".join(jd_required_parts),
        "candidate_has": ", ".join(candidate_skills) if candidate_skills else "No skills listed",
        "reasoning": reasoning,
        "matched": must_matched + nice_matched,
        "missing": must_missing + nice_missing,
    }


async def _score_experience_years(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score years of experience match (0-100) with detailed evidence."""
    required_raw = requirements.get("years_experience")
    candidate_raw = candidate.get("years_experience")

    if required_raw is None:
        return {
            "score": 100.0,
            "label": "Experience Years",
            "weight": FACTOR_WEIGHTS["experience_years"],
            "verdict": "strong",
            "jd_required": "No years requirement specified",
            "candidate_has": f"{candidate_raw} years" if candidate_raw is not None else "Unknown",
            "reasoning": "No experience requirement specified in the JD; defaulting to full score.",
            "matched": [],
            "missing": [],
        }

    if candidate_raw is None:
        return {
            "score": 0.0,
            "label": "Experience Years",
            "weight": FACTOR_WEIGHTS["experience_years"],
            "verdict": "missing",
            "jd_required": f"{required_raw}+ years",
            "candidate_has": "Years of experience not available from resume",
            "reasoning": "Could not determine candidate's years of experience from the resume.",
            "matched": [],
            "missing": ["years_experience"],
        }

    try:
        required = float(required_raw)
        actual = float(candidate_raw)
    except (TypeError, ValueError):
        return {
            "score": 0.0,
            "label": "Experience Years",
            "weight": FACTOR_WEIGHTS["experience_years"],
            "verdict": "missing",
            "jd_required": str(required_raw),
            "candidate_has": str(candidate_raw),
            "reasoning": "Could not parse years of experience as numbers.",
            "matched": [],
            "missing": [],
        }

    gap = required - actual

    if gap <= 0 and actual > required + 5:
        score = 90.0
        reasoning = (
            f"Candidate has {actual:.0f} years, JD requires {required:.0f}+ "
            f"-- exceeds requirement by {actual - required:.0f} years. "
            f"Slight overqualification flag."
        )
    elif gap <= 0:
        score = 100.0
        reasoning = (
            f"Candidate has {actual:.0f} years, JD requires {required:.0f}+ "
            f"-- exceeds requirement by {actual - required:.0f} years."
        )
    elif gap <= 1:
        score = 80.0
        reasoning = (
            f"Candidate has {actual:.0f} years, JD requires {required:.0f}+ "
            f"-- within 1 year of requirement."
        )
    elif gap <= 2:
        score = 60.0
        reasoning = (
            f"Candidate has {actual:.0f} years, JD requires {required:.0f}+ "
            f"-- {gap:.0f} years short of requirement."
        )
    else:
        score = 30.0
        reasoning = (
            f"Candidate has {actual:.0f} years, JD requires {required:.0f}+ "
            f"-- significantly below requirement (gap: {gap:.0f} years)."
        )

    return {
        "score": round(score, 2),
        "label": "Experience Years",
        "weight": FACTOR_WEIGHTS["experience_years"],
        "verdict": _verdict(score),
        "jd_required": f"{required:.0f}+ years of experience",
        "candidate_has": f"{actual:.0f} years of experience",
        "reasoning": reasoning,
        "matched": [],
        "missing": [],
    }


async def _score_experience_relevance(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score relevance of candidate's experience using LLM for cross-industry understanding."""
    from app.services import llm

    role_title = str(requirements.get("title") or "")
    responsibilities = requirements.get("responsibilities") or []
    candidate_experience = candidate.get("experience") or []
    candidate_industries = candidate.get("industries") or []
    candidate_summary = candidate.get("summary") or ""

    # Build concise experience summary for the LLM
    exp_lines = []
    for exp in candidate_experience[:6]:  # Top 6 roles
        if isinstance(exp, dict):
            title = exp.get("title", "")
            company = exp.get("company", "")
            highlights = exp.get("highlights", [])
            top_highlights = "; ".join(str(h) for h in highlights[:3])
            exp_lines.append(f"{title} at {company}: {top_highlights}")

    if not exp_lines and not candidate_summary:
        return {
            "score": 0.0, "label": "Experience Relevance",
            "weight": FACTOR_WEIGHTS["experience_relevance"], "verdict": "missing",
            "jd_required": role_title or "Not specified",
            "candidate_has": "No experience data available",
            "reasoning": "No candidate experience data to evaluate.", "matched": [], "missing": [],
        }

    try:
        result = await llm.extract_json(
            prompt=f"""JD Role: {role_title}
JD Responsibilities: {'; '.join(str(r) for r in responsibilities[:8])}
JD Must-have skills: {', '.join(requirements.get('must_have_skills') or [])}

Candidate Summary: {candidate_summary}
Candidate Industries: {', '.join(str(i) for i in candidate_industries)}
Candidate Experience:
{chr(10).join(exp_lines)}""",
            system="""You are evaluating how relevant a candidate's work experience is to a specific role.
Consider: industry alignment, responsibility overlap, domain expertise, and transferable experience.
A data engineer working in government/healthcare with Azure is highly relevant to a data engineering role in hospitality — the technical skills transfer.
Don't penalize industry differences if the core technical work is the same.

Return JSON:
{
  "score": 0-100,
  "relevant_experience": ["brief description of relevant experience points"],
  "gaps": ["areas where experience doesn't align"],
  "reasoning": "2-3 sentence assessment of how well their experience prepares them for this role"
}""",
        )

        score = float(result.get("score", 50))
        score = round(min(max(score, 0), 100), 2)
        relevant = result.get("relevant_experience", [])
        gaps = result.get("gaps", [])
        reasoning = result.get("reasoning", "")

    except Exception as e:
        logger.warning("LLM experience relevance failed, using fallback: %s", e)
        score = 50.0
        relevant = []
        gaps = []
        reasoning = "Could not assess experience relevance."

    return {
        "score": score,
        "label": "Experience Relevance",
        "weight": FACTOR_WEIGHTS["experience_relevance"],
        "verdict": _verdict(score),
        "jd_required": f"Role: {role_title}" + (f"; Key responsibilities: {', '.join(str(r) for r in responsibilities[:3])}" if responsibilities else ""),
        "candidate_has": f"Industries: {', '.join(str(i) for i in candidate_industries)}" if candidate_industries else candidate_summary[:100] if candidate_summary else "No domain data",
        "reasoning": reasoning,
        "matched": relevant,
        "missing": gaps,
    }


async def _score_education(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score education level and field match (0-100) with detailed evidence."""
    DEGREE_LEVELS: dict[str, int] = {
        "associate": 1, "associates": 1,
        "bachelor": 2, "bachelors": 2, "undergraduate": 2,
        "bs": 2, "ba": 2, "b.s.": 2, "b.a.": 2, "bsc": 2, "beng": 2, "b.eng": 2,
        "master": 3, "masters": 3, "ms": 3, "ma": 3, "m.s.": 3, "m.a.": 3, "mba": 3, "msc": 3,
        "phd": 4, "ph.d.": 4, "doctorate": 4, "doctoral": 4,
    }
    LEVEL_LABELS = {1: "Associate", 2: "Bachelor's", 3: "Master's", 4: "PhD"}

    TECHNICAL_FIELDS: set[str] = {
        "computer science", "cs", "software engineering", "electrical engineering",
        "information technology", "it", "mathematics", "math", "statistics",
        "data science", "physics", "engineering", "computer engineering",
        "information systems", "cybersecurity",
    }

    def _detect_level(text: str) -> int | None:
        text_lower = text.lower()
        best = None
        for keyword, level in DEGREE_LEVELS.items():
            if keyword in text_lower:
                if best is None or level > best:
                    best = level
        return best

    def _detect_field(text: str) -> str | None:
        text_lower = text.lower()
        for f in TECHNICAL_FIELDS:
            if f in text_lower:
                return f
        return None

    education_req_raw = requirements.get("education_requirements") or ""
    if isinstance(education_req_raw, list):
        education_req_raw = " ".join(str(x) for x in education_req_raw)

    edu_entries = candidate.get("education") or []
    if isinstance(edu_entries, str):
        education_candidate_raw = edu_entries
    elif isinstance(edu_entries, list):
        education_candidate_raw = " ".join(
            " ".join(str(v) for v in (e.values() if isinstance(e, dict) else [e]))
            for e in edu_entries
        )
    else:
        education_candidate_raw = str(edu_entries)

    # Build human-readable candidate education
    candidate_edu_display = []
    if isinstance(edu_entries, list):
        for e in edu_entries:
            if isinstance(e, dict):
                parts = []
                if e.get("degree"):
                    parts.append(str(e["degree"]))
                if e.get("field"):
                    parts.append(f"in {e['field']}")
                if e.get("institution"):
                    parts.append(f"from {e['institution']}")
                if parts:
                    candidate_edu_display.append(" ".join(parts))

    candidate_edu_str = "; ".join(candidate_edu_display) if candidate_edu_display else education_candidate_raw.strip() or "No education data"

    if not str(education_req_raw).strip():
        return {
            "score": 100.0,
            "label": "Education Match",
            "weight": FACTOR_WEIGHTS["education_match"],
            "verdict": "strong",
            "jd_required": "No education requirement specified",
            "candidate_has": candidate_edu_str,
            "reasoning": "No education requirement in the JD; defaulting to full score.",
            "matched": [],
            "missing": [],
        }

    if not education_candidate_raw.strip():
        return {
            "score": 0.0,
            "label": "Education Match",
            "weight": FACTOR_WEIGHTS["education_match"],
            "verdict": "missing",
            "jd_required": str(education_req_raw),
            "candidate_has": "No education information available",
            "reasoning": "Candidate education information not found in resume.",
            "matched": [],
            "missing": ["education"],
        }

    required_level = _detect_level(str(education_req_raw))
    candidate_level = _detect_level(education_candidate_raw)

    # Field matching
    required_field = _detect_field(str(education_req_raw))
    candidate_field = _detect_field(education_candidate_raw)
    is_technical_req = "technical" in str(education_req_raw).lower() or required_field is not None

    if required_level is None:
        # Can't parse level, give benefit of doubt
        score = 80.0
        reasoning = f"Could not parse required education level from '{education_req_raw}'. Candidate has: {candidate_edu_str}."
    elif candidate_level is None:
        score = 30.0
        reasoning = f"Could not determine candidate's degree level. Required: {LEVEL_LABELS.get(required_level, str(required_level))}."
    elif candidate_level >= required_level:
        score = 100.0
        reasoning = (
            f"Candidate holds {LEVEL_LABELS.get(candidate_level, str(candidate_level))} degree; "
            f"requirement is {LEVEL_LABELS.get(required_level, str(required_level))}. Meets or exceeds requirement."
        )
        # Check field match for bonus/penalty
        if is_technical_req and candidate_field:
            reasoning += f" Field match: {candidate_field}."
        elif is_technical_req and not candidate_field:
            score = 85.0
            reasoning += " However, degree field may not be a direct technical match."
    else:
        score = round((candidate_level / required_level) * 80.0, 2)
        reasoning = (
            f"Candidate holds {LEVEL_LABELS.get(candidate_level, str(candidate_level))} degree; "
            f"requirement is {LEVEL_LABELS.get(required_level, str(required_level))}. Below required level."
        )

    matched = []
    missing = []
    if candidate_level is not None and required_level is not None and candidate_level >= required_level:
        matched.append(LEVEL_LABELS.get(candidate_level, str(candidate_level)))
    elif required_level is not None:
        missing.append(LEVEL_LABELS.get(required_level, str(required_level)))

    return {
        "score": score,
        "label": "Education Match",
        "weight": FACTOR_WEIGHTS["education_match"],
        "verdict": _verdict(score),
        "jd_required": str(education_req_raw),
        "candidate_has": candidate_edu_str,
        "reasoning": reasoning,
        "matched": matched,
        "missing": missing,
    }


async def _score_title_seniority(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score title and seniority alignment (0-100)."""
    role_title = str(requirements.get("title") or "")
    seniority = str(requirements.get("seniority_level") or "")
    candidate_title = str(candidate.get("current_title") or "")

    if not role_title and not seniority:
        return {
            "score": 100.0,
            "label": "Title & Seniority",
            "weight": FACTOR_WEIGHTS["title_seniority"],
            "verdict": "strong",
            "jd_required": "No title/seniority specified",
            "candidate_has": candidate_title or "No title available",
            "reasoning": "No title or seniority requirement specified.",
            "matched": [],
            "missing": [],
        }

    if not candidate_title.strip():
        return {
            "score": 0.0,
            "label": "Title & Seniority",
            "weight": FACTOR_WEIGHTS["title_seniority"],
            "verdict": "missing",
            "jd_required": f"{role_title} ({seniority})" if seniority else role_title,
            "candidate_has": "No current title available",
            "reasoning": "Candidate's current title not available.",
            "matched": [],
            "missing": ["current_title"],
        }

    # Seniority comparison
    role_seniority_level = _detect_seniority(seniority or role_title)
    candidate_seniority_level = _detect_seniority(candidate_title)
    seniority_gap = abs(role_seniority_level - candidate_seniority_level)

    # Title keyword overlap
    STOPWORDS = {"and", "of", "the", "a", "an", "in", "at", "for", "to", "with", "on", "-", "/"}

    def _tokenize(text: str) -> set[str]:
        tokens = set(re.split(r"[\s\-/,]+", text.lower()))
        return tokens - STOPWORDS - {""}

    role_tokens = _tokenize(role_title)
    candidate_tokens = _tokenize(candidate_title)
    token_overlap = role_tokens & candidate_tokens
    token_ratio = len(token_overlap) / len(role_tokens) if role_tokens else 0.5

    # Combine seniority match + title relevance
    if seniority_gap == 0:
        seniority_score = 100.0
    elif seniority_gap == 1:
        seniority_score = 75.0
    elif seniority_gap == 2:
        seniority_score = 50.0
    else:
        seniority_score = max(20.0, 100.0 - seniority_gap * 20)

    title_relevance_score = min(token_ratio * 100.0, 100.0)
    score = round(seniority_score * 0.6 + title_relevance_score * 0.4, 2)

    # Determine direction
    if candidate_seniority_level > role_seniority_level:
        direction = "Candidate may be overqualified"
    elif candidate_seniority_level < role_seniority_level:
        direction = "Candidate may be under-leveled"
    else:
        direction = "Seniority level aligns"

    reasoning = (
        f"Candidate title '{candidate_title}' vs role '{role_title}' ({seniority or 'level not specified'}). "
        f"{direction}. Title keyword overlap: {len(token_overlap)}/{len(role_tokens)} tokens."
    )

    return {
        "score": score,
        "label": "Title & Seniority",
        "weight": FACTOR_WEIGHTS["title_seniority"],
        "verdict": _verdict(score),
        "jd_required": f"{role_title} ({seniority})" if seniority else role_title,
        "candidate_has": candidate_title,
        "reasoning": reasoning,
        "matched": list(token_overlap),
        "missing": list(role_tokens - candidate_tokens) if role_tokens else [],
    }


async def _score_leadership(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score leadership and management evidence (0-100)."""
    text_blob = _get_candidate_text_blob(candidate)
    leadership_evidence_list = candidate.get("leadership_evidence") or []

    # Check for leadership keywords in text
    found_keywords: list[str] = []
    for kw in LEADERSHIP_KEYWORDS:
        if kw in text_blob:
            found_keywords.append(kw)

    # Check for team size mentions
    team_size_pattern = re.compile(r'(\d+)\s*(?:person|people|member|engineer|developer|designer|report)', re.IGNORECASE)
    team_sizes = team_size_pattern.findall(text_blob)

    # Check if JD requires leadership
    jd_text = " ".join([
        str(requirements.get("title") or ""),
        " ".join(str(r) for r in (requirements.get("responsibilities") or [])),
        str(requirements.get("seniority_level") or ""),
    ]).lower()

    jd_needs_leadership = any(kw in jd_text for kw in [
        "lead", "manage", "leadership", "cross-functional", "mentor",
        "direct reports", "team", "people manager", "head of",
        "director", "vp", "manager",
    ])

    # Score
    evidence_count = len(found_keywords) + len(leadership_evidence_list)
    if evidence_count >= 5:
        score = 100.0
    elif evidence_count >= 3:
        score = 80.0
    elif evidence_count >= 1:
        score = 55.0
    else:
        score = 20.0 if jd_needs_leadership else 50.0

    if team_sizes:
        score = min(score + 10, 100.0)

    jd_required_str = "Leadership/management experience required" if jd_needs_leadership else "Leadership not explicitly required"

    candidate_has_parts = []
    if found_keywords:
        candidate_has_parts.append(f"Keywords found: {', '.join(found_keywords[:5])}")
    if team_sizes:
        candidate_has_parts.append(f"Team sizes mentioned: {', '.join(team_sizes[:3])}")
    if leadership_evidence_list:
        candidate_has_parts.append(f"Leadership evidence: {'; '.join(str(e) for e in leadership_evidence_list[:3])}")
    candidate_has_str = ". ".join(candidate_has_parts) if candidate_has_parts else "No leadership evidence found"

    reasoning = f"Found {evidence_count} leadership signal(s) in resume."
    if jd_needs_leadership and evidence_count == 0:
        reasoning += " JD requires leadership experience but none found."
    elif not jd_needs_leadership and evidence_count == 0:
        reasoning += " Leadership not explicitly required by JD."

    return {
        "score": round(score, 2),
        "label": "Leadership",
        "weight": FACTOR_WEIGHTS["leadership"],
        "verdict": _verdict(score),
        "jd_required": jd_required_str,
        "candidate_has": candidate_has_str,
        "reasoning": reasoning,
        "matched": found_keywords[:5],
        "missing": [],
    }


async def _score_impact(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score quantified impact evidence (0-100)."""
    text_blob = _get_candidate_text_blob(candidate)
    achievements = candidate.get("achievements") or []

    # Find impact patterns in text
    impact_matches: list[str] = []
    for pattern in IMPACT_PATTERNS:
        matches = pattern.findall(text_blob)
        impact_matches.extend(matches[:3])  # cap per pattern

    # Count unique impact signals
    total_signals = len(set(impact_matches)) + len(achievements)

    if total_signals >= 8:
        score = 100.0
    elif total_signals >= 5:
        score = 85.0
    elif total_signals >= 3:
        score = 70.0
    elif total_signals >= 1:
        score = 45.0
    else:
        score = 15.0

    candidate_has_parts = []
    if achievements:
        candidate_has_parts.append(f"Achievements: {'; '.join(str(a) for a in achievements[:3])}")
    if impact_matches:
        unique_matches = list(set(impact_matches))[:5]
        candidate_has_parts.append(f"Impact signals: {', '.join(str(m) for m in unique_matches)}")
    candidate_has_str = ". ".join(candidate_has_parts) if candidate_has_parts else "No quantified impact found"

    reasoning = f"Found {total_signals} quantified impact signal(s) in resume."
    if total_signals == 0:
        reasoning += " Resume lacks concrete metrics, percentages, or quantified outcomes."

    return {
        "score": round(score, 2),
        "label": "Impact Evidence",
        "weight": FACTOR_WEIGHTS["impact_evidence"],
        "verdict": _verdict(score),
        "jd_required": "Quantified achievements and measurable outcomes",
        "candidate_has": candidate_has_str,
        "reasoning": reasoning,
        "matched": [str(m) for m in set(impact_matches)][:5],
        "missing": [],
    }


async def _score_location(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """Score location/remote compatibility (0-100)."""
    remote_policy = str(requirements.get("remote_policy") or "").lower().strip()
    candidate_location = str(candidate.get("location") or "").lower().strip()
    role_location = str(requirements.get("location") or "").lower().strip()

    jd_required_str = f"{role_location or 'Not specified'} ({remote_policy or 'not specified'})"
    candidate_has_str = candidate_location or "Location not provided"

    # Fully remote role: everyone qualifies
    if remote_policy in {"remote", "fully remote", "fully-remote", "100% remote"}:
        return {
            "score": 100.0,
            "label": "Location Fit",
            "weight": FACTOR_WEIGHTS["location_fit"],
            "verdict": "strong",
            "jd_required": jd_required_str,
            "candidate_has": candidate_has_str,
            "reasoning": "Role is fully remote; all locations match.",
            "matched": [],
            "missing": [],
        }

    # Candidate says remote-flexible
    if candidate_location in {"remote", "anywhere", "flexible"}:
        if remote_policy in {"hybrid", "flexible"}:
            return {
                "score": 85.0,
                "label": "Location Fit",
                "weight": FACTOR_WEIGHTS["location_fit"],
                "verdict": "strong",
                "jd_required": jd_required_str,
                "candidate_has": candidate_has_str,
                "reasoning": "Candidate is remote-flexible and role supports hybrid/flexible work.",
                "matched": [],
                "missing": [],
            }
        return {
            "score": 50.0,
            "label": "Location Fit",
            "weight": FACTOR_WEIGHTS["location_fit"],
            "verdict": "weak",
            "jd_required": jd_required_str,
            "candidate_has": candidate_has_str,
            "reasoning": f"Candidate is remote-flexible but role policy is '{remote_policy or 'on-site'}'.",
            "matched": [],
            "missing": [],
        }

    if not candidate_location or not role_location:
        return {
            "score": 50.0,
            "label": "Location Fit",
            "weight": FACTOR_WEIGHTS["location_fit"],
            "verdict": "partial",
            "jd_required": jd_required_str,
            "candidate_has": candidate_has_str,
            "reasoning": "Location information incomplete; defaulting to neutral score.",
            "matched": [],
            "missing": [],
        }

    # Compare tokens for city/country matching
    candidate_tokens = set(candidate_location.replace(",", " ").split())
    role_tokens = set(role_location.replace(",", " ").split())
    common = candidate_tokens & role_tokens

    if len(common) >= 2 or candidate_location == role_location:
        score = 100.0
        reasoning = f"Candidate location '{candidate_location}' closely matches role location '{role_location}'."
    elif len(common) == 1:
        score = 75.0
        reasoning = (
            f"Candidate location '{candidate_location}' partially matches role location "
            f"'{role_location}' (shared: '{next(iter(common))}')."
        )
    else:
        if remote_policy in {"hybrid", "flexible"}:
            score = 50.0
            reasoning = (
                f"Candidate in '{candidate_location}' doesn't match '{role_location}', "
                f"but role has {remote_policy} policy."
            )
        else:
            score = 30.0
            reasoning = (
                f"Candidate in '{candidate_location}' doesn't match '{role_location}' "
                f"and no remote option indicated."
            )

    return {
        "score": round(score, 2),
        "label": "Location Fit",
        "weight": FACTOR_WEIGHTS["location_fit"],
        "verdict": _verdict(score),
        "jd_required": jd_required_str,
        "candidate_has": candidate_has_str,
        "reasoning": reasoning,
        "matched": list(common),
        "missing": [],
    }


# ---------------------------------------------------------------------------
# Evidence-based signal builders
# ---------------------------------------------------------------------------


def _build_strengths(
    factor_scores: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> list[str]:
    """Generate evidence-based strength statements."""
    strengths: list[str] = []

    # Skills
    skills = factor_scores.get("skills_match", {})
    if skills.get("score", 0) >= 75:
        matched = skills.get("matched", [])
        if matched:
            strengths.append(
                f"Strong skills alignment: matches {len(matched)} required skills including {', '.join(matched[:4])}"
            )

    # Experience years
    exp = factor_scores.get("experience_years", {})
    if exp.get("score", 0) >= 80:
        candidate_years = candidate.get("years_experience")
        required_years = requirements.get("years_experience")
        if candidate_years is not None and required_years is not None:
            # List companies worked at (not just current) to avoid false attribution
            companies = []
            for role in (candidate.get("experience") or [])[:4]:
                if isinstance(role, dict) and role.get("company"):
                    c = str(role["company"]).strip()
                    if c and c not in companies:
                        companies.append(c)
            company_str = f" across {', '.join(companies)}" if len(companies) > 1 else f" (currently at {companies[0]})" if companies else ""
            strengths.append(
                f"{candidate_years} years of experience{company_str} — "
                f"{'exceeds' if float(candidate_years) > float(required_years) else 'meets'} "
                f"the {required_years}-year requirement"
            )

    # Experience relevance
    relevance = factor_scores.get("experience_relevance", {})
    if relevance.get("score", 0) >= 70:
        matched_domains = relevance.get("matched", [])
        if matched_domains:
            strengths.append(f"Relevant domain experience in {', '.join(matched_domains)}")

    # Education
    edu = factor_scores.get("education_match", {})
    if edu.get("score", 0) >= 80:
        candidate_edu = edu.get("candidate_has", "")
        if candidate_edu and candidate_edu != "No education data":
            strengths.append(f"Education meets requirements: {candidate_edu}")

    # Title seniority
    title = factor_scores.get("title_seniority", {})
    if title.get("score", 0) >= 75:
        candidate_title = candidate.get("current_title", "")
        if candidate_title:
            strengths.append(f"Current title '{candidate_title}' aligns with role seniority level")

    # Leadership
    leadership = factor_scores.get("leadership", {})
    if leadership.get("score", 0) >= 70:
        matched_kw = leadership.get("matched", [])
        if matched_kw:
            strengths.append(
                f"Leadership evidence found: {', '.join(matched_kw[:3])}"
            )

    # Impact
    impact = factor_scores.get("impact_evidence", {})
    if impact.get("score", 0) >= 70:
        candidate_impact = impact.get("candidate_has", "")
        if candidate_impact and candidate_impact != "No quantified impact found":
            strengths.append(f"Quantified impact: {candidate_impact[:150]}")

    # Location
    loc = factor_scores.get("location_fit", {})
    if loc.get("score", 0) >= 85:
        strengths.append(f"Location compatible: {loc.get('reasoning', '')}")

    return strengths


def _build_risks(
    factor_scores: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> list[str]:
    """Generate evidence-based risk/gap warnings."""
    risks: list[str] = []

    # Skills
    skills = factor_scores.get("skills_match", {})
    missing_skills = skills.get("missing", [])
    if missing_skills:
        # Separate must-have vs nice-to-have missing
        must_have = [s.strip() for s in (requirements.get("must_have_skills") or []) if s]
        must_have_lower = {s.lower() for s in must_have}
        must_missing = [s for s in missing_skills if s.lower() in must_have_lower]
        nice_missing = [s for s in missing_skills if s.lower() not in must_have_lower]

        if must_missing:
            risks.append(f"Missing must-have skills: {', '.join(must_missing)}")
        if nice_missing:
            risks.append(f"Missing nice-to-have skills: {', '.join(nice_missing)}")

    # Experience years
    exp = factor_scores.get("experience_years", {})
    if exp.get("score", 0) < 70:
        risks.append(exp.get("reasoning", "Experience years below requirement"))

    # Experience relevance
    relevance = factor_scores.get("experience_relevance", {})
    missing_domains = relevance.get("missing", [])
    if missing_domains:
        risks.append(f"No experience found in required domains: {', '.join(missing_domains)}")
    elif relevance.get("score", 0) < 60:
        risks.append("Limited relevance between candidate's experience and role requirements")

    # Education
    edu = factor_scores.get("education_match", {})
    if edu.get("score", 0) < 70:
        risks.append(
            f"Education gap: JD requires '{edu.get('jd_required', 'N/A')}', "
            f"candidate has '{edu.get('candidate_has', 'N/A')}'"
        )

    # Title seniority
    title = factor_scores.get("title_seniority", {})
    if title.get("score", 0) < 60:
        risks.append(title.get("reasoning", "Title/seniority misalignment"))

    # Leadership
    leadership = factor_scores.get("leadership", {})
    if leadership.get("score", 0) < 50 and "required" in leadership.get("jd_required", "").lower():
        risks.append("No leadership or management experience found -- JD requires this")

    # Impact
    impact = factor_scores.get("impact_evidence", {})
    if impact.get("score", 0) < 50:
        risks.append("Resume lacks quantified achievements or measurable outcomes")

    # Location
    loc = factor_scores.get("location_fit", {})
    if loc.get("score", 0) < 60:
        risks.append(loc.get("reasoning", "Location mismatch"))

    return risks


def _build_missing_evidence(
    factor_scores: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
) -> list[str]:
    """Identify fields where candidate data is missing or insufficient."""
    missing: list[str] = []

    FIELD_CHECKS: dict[str, str] = {
        "skills": "Skills list",
        "years_experience": "Years of experience",
        "education": "Education history",
        "current_title": "Current job title",
        "location": "Location",
        "experience": "Work experience",
        "achievements": "Quantified achievements",
        "leadership_evidence": "Leadership evidence",
        "industries": "Industry/domain experience",
    }

    for field_name, label in FIELD_CHECKS.items():
        value = candidate.get(field_name)
        if value is None:
            missing.append(f"{label}: not found in resume")
        elif isinstance(value, list) and len(value) == 0:
            missing.append(f"{label}: no entries extracted from resume")
        elif isinstance(value, str) and not value.strip():
            missing.append(f"{label}: empty in resume data")

    return missing


def _build_summary(
    overall: float,
    factor_scores: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> str:
    """Build a 2-3 sentence recruiter-friendly summary."""
    recommendation = _compute_recommendation(overall)
    rec_label = {
        "strong_yes": "Strong match",
        "yes": "Good match",
        "maybe": "Potential match with gaps",
        "no": "Weak match",
    }.get(recommendation, "Match assessment")

    name = candidate.get("name") or "This candidate"
    title = candidate.get("current_title") or ""
    company = candidate.get("current_company") or ""
    years = candidate.get("years_experience")
    role_title = requirements.get("title") or "this role"

    # Build intro
    intro_parts = [name]
    if title and company:
        intro_parts.append(f"({title} at {company})")
    elif title:
        intro_parts.append(f"({title})")

    intro = " ".join(intro_parts)

    # Find top strengths and weaknesses
    sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    top_strength = sorted_factors[0] if sorted_factors else None
    top_weakness = sorted_factors[-1] if sorted_factors else None

    sentences = [f"{rec_label}."]

    # Experience sentence — list multiple companies, don't attribute all years to one
    if years is not None:
        companies = []
        for role in (candidate.get("experience") or [])[:4]:
            if isinstance(role, dict) and role.get("company"):
                c = str(role["company"]).strip()
                if c and c not in companies:
                    companies.append(c)
        exp_str = f"{intro} brings {years} years of experience"
        if len(companies) > 1:
            exp_str += f" across {', '.join(companies[:3])}"
            if len(companies) > 3:
                exp_str += f" and {len(companies) - 3} more"
        elif companies:
            exp_str += f", most recently at {companies[0]}"
        sentences.append(exp_str + ".")
    else:
        sentences.append(f"{intro} is being evaluated for {role_title}.")

    # Key strength/gap
    if top_strength and top_strength[1].get("score", 0) >= 70:
        sentences.append(f"Key strength: {top_strength[1].get('label', '')} ({top_strength[1].get('verdict', '')}).")

    if top_weakness and top_weakness[1].get("score", 0) < 60:
        sentences.append(f"Main gap: {top_weakness[1].get('label', '')} ({top_weakness[1].get('reasoning', '')[:80]}).")

    return " ".join(sentences[:4])  # Cap at 4 sentences
