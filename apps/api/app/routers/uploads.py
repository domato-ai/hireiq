from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument
from app.services.storage import StorageService
from app.workers.parse_resume import enqueue_parse_resume

router = APIRouter(prefix="/uploads", tags=["uploads"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UploadedDocument(BaseModel):
    document_id: uuid.UUID
    candidate_id: uuid.UUID
    filename: str
    blob_url: str
    size_bytes: int


class ResumeUploadResponse(BaseModel):
    uploaded: list[UploadedDocument]
    skipped: list[str]  # filenames that were rejected


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/resumes",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more resume files for a role",
)
async def upload_resumes(
    role_id: uuid.UUID,
    files: Annotated[list[UploadFile], File(description="PDF or DOCX resume files (max 10 MB each)")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(StorageService.from_settings)],
) -> Any:
    """
    Accepts a multi-file upload of resumes (PDF / DOCX).

    For each valid file the handler:
    1. Validates MIME type and file size.
    2. Uploads the raw file to Azure Blob Storage.
    3. Creates a `Candidate` record (status=pending) and a linked
       `CandidateDocument` record in the database.
    4. Enqueues a background job to extract text and generate embeddings.

    Files that fail validation are collected in the `skipped` list and
    processing continues for the remaining files.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided."
        )

    uploaded: list[UploadedDocument] = []
    skipped: list[str] = []

    for upload in files:
        filename = upload.filename or "unknown"

        # ---- Validate MIME type ----
        if upload.content_type not in ALLOWED_MIME_TYPES:
            skipped.append(filename)
            continue

        # ---- Read and size-check ----
        content = await upload.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            skipped.append(filename)
            continue

        # ---- Upload to Blob Storage ----
        blob_name = f"resumes/{role_id}/{uuid.uuid4()}/{filename}"
        blob_url = await storage.upload(
            container="resumes",
            blob_name=blob_name,
            data=content,
            content_type=upload.content_type or "application/octet-stream",
        )

        # ---- Persist Candidate + CandidateDocument ----
        candidate = Candidate(role_id=role_id, status="pending")
        db.add(candidate)
        await db.flush()  # obtain candidate.id

        doc = CandidateDocument(
            candidate_id=candidate.id,
            filename=filename,
            blob_url=blob_url,
            file_type=upload.content_type or "application/octet-stream",
            size_bytes=len(content),
        )
        db.add(doc)
        await db.flush()

        # ---- Enqueue parsing background task ----
        background_tasks.add_task(enqueue_parse_resume, str(candidate.id), blob_url)

        uploaded.append(
            UploadedDocument(
                document_id=doc.id,
                candidate_id=candidate.id,
                filename=filename,
                blob_url=blob_url,
                size_bytes=len(content),
            )
        )

    return ResumeUploadResponse(uploaded=uploaded, skipped=skipped)
