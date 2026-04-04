"""Resume and JD structured extraction service."""
from __future__ import annotations
import re
import logging
from app.services import llm

logger = logging.getLogger(__name__)

# ── Tier 1: Regex extraction (free) ──

def extract_contact_info(text: str) -> dict:
    """Extract name, email, phone, LinkedIn from resume text using regex."""
    result = {"name": None, "email": None, "phone": None, "linkedin": None}

    # Email
    email_match = re.search(r'\b[\w.+-]+@[\w-]+\.[\w.]+\b', text)
    if email_match:
        result["email"] = email_match.group(0).lower()

    # Phone (various formats)
    phone_match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

    # LinkedIn
    linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
    if linkedin_match:
        result["linkedin"] = "https://" + linkedin_match.group(0)

    # Name — heuristic: first non-empty line that's not an email/phone/URL
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:  # Check first 5 lines
        if '@' in line or 'http' in line.lower() or re.match(r'^[\d\+\(]', line):
            continue
        if len(line) < 50 and len(line.split()) <= 4:
            result["name"] = line
            break

    return result

# ── Tier 2: LLM extraction (GPT-4o-mini) ──

RESUME_EXTRACTION_SYSTEM = """You are a precise and thorough resume parser. Your job is to extract EVERY relevant piece of information from the resume.

CRITICAL: Scan the ENTIRE resume — not just a skills section. Extract technologies, tools, platforms, and frameworks mentioned in:
- Career synopsis / summary sections
- Individual role descriptions and responsibilities
- Project details and achievements
- Certifications and training

Return a JSON object with these exact fields:
{
  "name": "Full name",
  "current_title": "Most recent job title",
  "current_company": "Most recent employer",
  "location": "City, State/Country or Remote",
  "years_experience": number (calculate from career history if not stated explicitly),
  "skills": ["skill1", "skill2", ...],
  "technologies": ["tech1", "tech2", ...],
  "education": [{"degree": "...", "field": "...", "institution": "...", "year": number or null}],
  "experience": [{"title": "...", "company": "...", "duration": "...", "highlights": ["..."]}],
  "certifications": ["cert1", ...],
  "summary": "2-3 sentence professional summary capturing their strongest value proposition",
  "achievements": ["Full context phrase of quantified achievement", ...],
  "leadership_evidence": ["Full context phrase of leadership/management mention", ...],
  "industries": ["Industry or domain worked in", ...]
}

For "skills": Include BOTH soft skills (leadership, stakeholder management, agile) AND technical skills. Cast a wide net.
For "technologies": Extract ALL technologies, tools, platforms, languages, frameworks, and cloud services mentioned ANYWHERE in the resume. Examples: Azure Data Factory, PySpark, Python, SQL, Databricks, Power BI, CI/CD, Azure DevOps, REST APIs, PostgreSQL, Docker, Kubernetes, Terraform, etc. Be exhaustive — scan every line.
For "experience": Include ALL roles, not just the most recent. Include company name, title, and 2-3 key highlights per role.
For "achievements": Extract ALL quantified results, metrics, percentages, and measurable outcomes. Include full context.
For "leadership_evidence": Extract ALL mentions of team leadership, mentoring, managing, team sizes, direct reports, agile delivery management.
For "industries": Extract ALL industries/domains/verticals from company descriptions and role contexts.
For "years_experience": Calculate total years from the earliest role to the most recent. If stated in summary (e.g. "17+ years"), use that number.

Be thorough. A recruiter is relying on this extraction to match candidates to jobs. Missing a key skill or technology means the candidate could be unfairly rejected.
Only include information explicitly stated. Do not fabricate. Use empty arrays [] for missing lists."""

async def extract_resume_structured(raw_text: str) -> dict:
    """Extract structured data from resume text using regex + LLM."""
    # Tier 1: regex for contact info
    contact = extract_contact_info(raw_text)

    # Tier 2: LLM for skills, experience, education
    # Send up to 12000 chars to capture full career history
    # GPT-4o-mini supports 128k context, so this is well within limits
    resume_text = raw_text[:12000] if len(raw_text) > 12000 else raw_text
    try:
        llm_result = await llm.extract_json(
            prompt=f"Parse this resume thoroughly. Extract ALL skills, technologies, tools, platforms, and frameworks mentioned anywhere in the resume — not just a skills section. Scan every role's responsibilities and achievements for technical skills.\n\n{resume_text}",
            system=RESUME_EXTRACTION_SYSTEM,
        )
    except Exception as e:
        logger.error("LLM extraction failed: %s", e)
        llm_result = {}

    # Merge: regex contact info takes priority for name/email
    if contact["name"] and not llm_result.get("name"):
        llm_result["name"] = contact["name"]
    if contact["email"]:
        llm_result["email"] = contact["email"]
    if contact["phone"]:
        llm_result["phone"] = contact["phone"]
    if contact["linkedin"]:
        llm_result["linkedin"] = contact["linkedin"]

    return llm_result

# ── JD extraction ──

JD_EXTRACTION_SYSTEM = """You are a precise job description parser. Extract structured requirements.
Return a JSON object with these exact fields:
{
  "title": "Job title",
  "must_have_skills": ["skill1", "skill2", ...],
  "nice_to_have_skills": ["skill1", ...],
  "years_experience": number or null,
  "education_requirements": ["requirement1", ...],
  "responsibilities": ["resp1", ...],
  "location": "location or Remote",
  "remote_policy": "remote" | "hybrid" | "onsite" | "unknown",
  "seniority_level": "junior" | "mid" | "senior" | "staff" | "director" | "vp" | "unknown"
}
Only include information explicitly stated. Use null/empty arrays for missing fields."""

async def extract_jd_requirements(jd_text: str) -> dict:
    """Extract structured requirements from a job description."""
    try:
        return await llm.extract_json(
            prompt=f"Parse this job description:\n\n{jd_text[:4000]}",
            system=JD_EXTRACTION_SYSTEM,
        )
    except Exception as e:
        logger.error("JD extraction failed: %s", e)
        return {}
