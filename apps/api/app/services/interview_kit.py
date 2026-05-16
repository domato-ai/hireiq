"""Interview kit + phone-screen generation grounded in the scoring output.

Reuses the candidate's already-extracted structured profile and the JD
requirements that the analyzer produced. Both functions return structured
JSON suitable for direct rendering on the candidate card.
"""
from __future__ import annotations

import logging
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)


def _candidate_snapshot(candidate: dict[str, Any]) -> str:
    """Compact prompt snippet — only the fields that matter for question generation."""
    parts: list[str] = []
    if candidate.get("name"):
        parts.append(f"Name: {candidate['name']}")
    if candidate.get("current_title") or candidate.get("current_company"):
        title = candidate.get("current_title") or ""
        company = candidate.get("current_company") or ""
        parts.append(f"Current: {title} at {company}".strip())
    if candidate.get("years_experience") is not None:
        parts.append(f"Years: {candidate['years_experience']}")

    exp = candidate.get("experience") or []
    if isinstance(exp, list) and exp:
        roles: list[str] = []
        for r in exp[:4]:
            if isinstance(r, dict):
                t, c = r.get("title", ""), r.get("company", "")
                hl = r.get("highlights") or []
                top = "; ".join(str(h) for h in hl[:2])
                roles.append(f"- {t} @ {c}: {top}".strip())
        if roles:
            parts.append("Experience:\n" + "\n".join(roles))

    skills = candidate.get("skills") or []
    if skills:
        parts.append("Skills: " + ", ".join(str(s) for s in skills[:20]))

    return "\n".join(parts)


def _jd_snapshot(jd: dict[str, Any]) -> str:
    parts: list[str] = []
    if jd.get("title"):
        parts.append(f"Role: {jd['title']}")
    if jd.get("seniority_level"):
        parts.append(f"Seniority: {jd['seniority_level']}")
    must = jd.get("must_have_skills") or []
    if must:
        parts.append("Must-have: " + ", ".join(str(s) for s in must))
    resp = jd.get("responsibilities") or []
    if resp:
        parts.append("Key responsibilities: " + "; ".join(str(r) for r in resp[:6]))
    return "\n".join(parts)


async def generate_interview_kit(
    candidate: dict[str, Any],
    jd_requirements: dict[str, Any],
    strengths: list[str] | None = None,
    risks: list[str] | None = None,
    missing_evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a tailored interview kit.

    Returns:
        {
          "behavioral": [{"question": str, "what_to_listen_for": str, "anchor": str}],
          "technical":  [{"question": str, "what_to_listen_for": str, "targets_gap": str}],
          "scorecard":  [{"competency": str, "definition": str}],
        }
    """
    strengths = strengths or []
    risks = risks or []
    missing_evidence = missing_evidence or []

    system = (
        "You are an expert technical recruiter helping a hiring manager prepare an interview. "
        "Generate questions that are specific to THIS candidate and THIS role — never generic. "
        "Each behavioral question must reference a concrete experience or claim from the resume. "
        "Each technical question must target a specific gap or risk identified for this candidate. "
        "Output strictly valid JSON in the requested shape — no prose outside the JSON."
    )

    prompt = f"""## Job
{_jd_snapshot(jd_requirements)}

## Candidate
{_candidate_snapshot(candidate)}

## Scorer-identified strengths
{chr(10).join(f"- {s}" for s in strengths[:6]) or "(none)"}

## Scorer-identified risks / gaps
{chr(10).join(f"- {r}" for r in risks[:6]) or "(none)"}

## Missing evidence (things to probe for)
{chr(10).join(f"- {m}" for m in missing_evidence[:6]) or "(none)"}

Return JSON in this exact shape:
{{
  "behavioral": [
    {{
      "question": "A specific behavioral question grounded in the candidate's actual experience.",
      "what_to_listen_for": "1-line: what a strong answer includes.",
      "anchor": "Which resume claim or scorer-strength this question is built on."
    }}
  ],
  "technical": [
    {{
      "question": "A specific role-relevant technical question.",
      "what_to_listen_for": "1-line: what a strong answer includes.",
      "targets_gap": "Which scorer-identified risk or missing-evidence item this probes."
    }}
  ],
  "scorecard": [
    {{
      "competency": "Short label, e.g. 'Stakeholder management'",
      "definition": "1-line rubric for what 'strong' looks like for THIS role."
    }}
  ]
}}

Constraints:
- Exactly 5 behavioral questions.
- Exactly 3 technical questions (each must reference a different gap/risk if any exist).
- Exactly 5 scorecard competencies drawn from the role's must-haves + responsibilities.
- Never invent candidate experiences they don't have. If you can't anchor a question, use the role context instead and say so in 'anchor'."""

    try:
        result = await llm.extract_json(prompt=prompt, system=system)
    except Exception as e:
        logger.warning("Interview kit generation failed: %s", e)
        return {"behavioral": [], "technical": [], "scorecard": [], "error": "generation_failed"}

    # Defensive shape coercion
    return {
        "behavioral": list(result.get("behavioral") or [])[:5],
        "technical": list(result.get("technical") or [])[:3],
        "scorecard": list(result.get("scorecard") or [])[:5],
    }


async def generate_phone_screen(
    candidate: dict[str, Any],
    jd_requirements: dict[str, Any],
    risks: list[str] | None = None,
    missing_evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a 5-7 question phone-screen script targeting the biggest unknowns.

    Returns:
        {
          "opener": str,                 # one-line warm opener
          "questions": [{"question": str, "why": str}],
          "closer": str,                 # next-step line
        }
    """
    risks = risks or []
    missing_evidence = missing_evidence or []

    system = (
        "You are an experienced recruiter writing a short, conversational phone-screen script. "
        "The goal is to qualify or disqualify the candidate in 15 minutes. "
        "Every question should resolve a concrete unknown — not waste the call on intros. "
        "Output strictly valid JSON."
    )

    prompt = f"""## Job
{_jd_snapshot(jd_requirements)}

## Candidate
{_candidate_snapshot(candidate)}

## Things the scorer flagged as risks
{chr(10).join(f"- {r}" for r in risks[:6]) or "(none)"}

## Missing evidence to probe
{chr(10).join(f"- {m}" for m in missing_evidence[:6]) or "(none)"}

Return JSON:
{{
  "opener": "A single warm one-liner the recruiter can read verbatim.",
  "questions": [
    {{
      "question": "A direct phone-screen question (conversational, short).",
      "why": "1-line: what unknown this resolves."
    }}
  ],
  "closer": "A single next-step line the recruiter says at the end."
}}

Constraints:
- Between 5 and 7 questions total.
- The first 1-2 questions confirm logistics (notice period, salary band, location/remote, work rights) — only those NOT already on the resume.
- The remaining 3-5 questions probe the scorer-flagged risks and missing-evidence items in order of importance.
- Never ask things the resume already answers."""

    try:
        result = await llm.extract_json(prompt=prompt, system=system)
    except Exception as e:
        logger.warning("Phone screen generation failed: %s", e)
        return {"opener": "", "questions": [], "closer": "", "error": "generation_failed"}

    questions = list(result.get("questions") or [])[:7]
    return {
        "opener": str(result.get("opener") or ""),
        "questions": questions,
        "closer": str(result.get("closer") or ""),
    }
