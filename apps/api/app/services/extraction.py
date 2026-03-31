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

RESUME_EXTRACTION_SYSTEM = """You are a precise resume parser. Extract structured information from the resume text.
Return a JSON object with these exact fields:
{
  "name": "Full name",
  "current_title": "Most recent job title",
  "current_company": "Most recent employer",
  "location": "City, State/Country or Remote",
  "years_experience": number or null,
  "skills": ["skill1", "skill2", ...],
  "education": [{"degree": "...", "field": "...", "institution": "...", "year": number or null}],
  "experience": [{"title": "...", "company": "...", "duration": "...", "highlights": ["..."]}],
  "certifications": ["cert1", ...],
  "summary": "1-2 sentence professional summary"
}
Only include information explicitly stated in the resume. Use null for missing fields. Do not infer or fabricate."""

async def extract_resume_structured(raw_text: str) -> dict:
    """Extract structured data from resume text using regex + LLM."""
    # Tier 1: regex for contact info
    contact = extract_contact_info(raw_text)

    # Tier 2: LLM for skills, experience, education
    try:
        llm_result = await llm.extract_json(
            prompt=f"Parse this resume:\n\n{raw_text[:4000]}",  # Cap at ~4000 chars
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
