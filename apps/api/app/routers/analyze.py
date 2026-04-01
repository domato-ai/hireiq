"""Analysis endpoint — the core product flow."""
from __future__ import annotations
import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.parser import extract_text
from app.services.extraction import extract_resume_structured, extract_jd_requirements
from app.services.embeddings import generate as generate_embedding
from app.services.scoring import score_candidate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])


class FactorDetail(BaseModel):
    score: float
    label: str
    weight: float
    verdict: str  # strong/partial/weak/missing
    jd_required: str
    candidate_has: str
    reasoning: str
    matched: list[str] = []
    missing: list[str] = []


class CandidateResult(BaseModel):
    id: str
    name: str | None
    current_title: str | None
    current_company: str | None
    location: str | None
    years_experience: int | None
    overall_score: float
    recommendation: str
    summary: str
    factor_scores: dict[str, FactorDetail]
    strengths: list[str]
    risks: list[str]
    missing_evidence: list[str]


class AnalysisResponse(BaseModel):
    analysis_id: str
    jd_requirements: dict
    candidates: list[CandidateResult]
    total_processed: int
    total_skipped: int


@router.post("", response_model=AnalysisResponse, status_code=200)
async def analyze(
    jd_text: Annotated[str, Form(description="Job description text")],
    files: list[UploadFile] = File(description="Resume files (PDF/DOCX)"),
):
    """
    Full analysis pipeline:
    1. Parse JD → extract requirements
    2. For each resume file → extract text → extract structured data → score
    3. Return ranked candidates
    """
    if not jd_text or len(jd_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description is too short")

    if not files:
        raise HTTPException(status_code=400, detail="No resume files provided")

    analysis_id = str(uuid.uuid4())[:8]

    # Step 1: Extract JD requirements
    logger.info("[%s] Extracting JD requirements...", analysis_id)
    jd_requirements = await extract_jd_requirements(jd_text)

    # Step 2: Process each resume
    candidates: list[CandidateResult] = []
    skipped = 0

    ALLOWED_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    for i, file in enumerate(files):
        filename = file.filename or f"resume_{i}"

        # Validate file type
        if file.content_type not in ALLOWED_TYPES:
            logger.warning("[%s] Skipping %s: unsupported type %s", analysis_id, filename, file.content_type)
            skipped += 1
            continue

        try:
            # Read file
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:  # 10MB limit
                skipped += 1
                continue

            # Extract text from PDF/DOCX
            logger.info("[%s] Extracting text from %s...", analysis_id, filename)
            raw_text = await extract_text(content, file.content_type or "application/octet-stream")

            if not raw_text or len(raw_text.strip()) < 50:
                logger.warning("[%s] %s: extracted text too short", analysis_id, filename)
                skipped += 1
                continue

            # Extract structured data
            logger.info("[%s] Extracting structured data from %s...", analysis_id, filename)
            structured = await extract_resume_structured(raw_text)

            # Score against JD
            logger.info("[%s] Scoring %s...", analysis_id, filename)
            scoring_result = await score_candidate(structured, jd_requirements)

            # Convert factor_scores dicts to FactorDetail models
            factor_details = {
                name: FactorDetail(**detail)
                for name, detail in scoring_result.factor_scores.items()
            }

            candidates.append(CandidateResult(
                id=str(uuid.uuid4())[:8],
                name=structured.get("name"),
                current_title=structured.get("current_title"),
                current_company=structured.get("current_company"),
                location=structured.get("location"),
                years_experience=structured.get("years_experience"),
                overall_score=scoring_result.overall_score,
                recommendation=scoring_result.recommendation,
                summary=scoring_result.summary,
                factor_scores=factor_details,
                strengths=scoring_result.strengths,
                risks=scoring_result.risks,
                missing_evidence=scoring_result.missing_evidence,
            ))

        except Exception as e:
            logger.error("[%s] Failed to process %s: %s", analysis_id, filename, e)
            skipped += 1
            continue

    # Sort by score descending
    candidates.sort(key=lambda c: c.overall_score, reverse=True)

    logger.info("[%s] Analysis complete: %d candidates, %d skipped",
                analysis_id, len(candidates), skipped)

    return AnalysisResponse(
        analysis_id=analysis_id,
        jd_requirements=jd_requirements,
        candidates=candidates,
        total_processed=len(candidates),
        total_skipped=skipped,
    )
