from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore
from app.models.role import Role
from app.models.workspace import Workspace

router = APIRouter(
    prefix="/workspaces/{workspace_id}/roles/{role_id}/candidates",
    tags=["candidates"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    overall_score: float
    factor_scores_json: dict[str, Any] | None
    reasons_json: dict[str, Any] | None
    strengths: list[str] | None
    risks: list[str] | None
    missing_evidence: list[str] | None
    created_at: Any


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_id: uuid.UUID
    name: str | None
    email: str | None
    structured_json: dict[str, Any] | None
    status: str
    created_at: Any
    scores: list[ScoreOut]


class ShortlistRequest(BaseModel):
    candidate_ids: list[uuid.UUID]


class CompareRequest(BaseModel):
    candidate_ids: list[uuid.UUID]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    user: CurrentUser,
    db: AsyncSession,
) -> Role:
    result = await db.execute(
        select(Role)
        .join(Workspace, Role.workspace_id == Workspace.id)
        .where(
            Role.id == role_id,
            Role.workspace_id == workspace_id,
            Workspace.owner_id == user.id,
        )
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return role


async def _get_candidate_or_404(
    candidate_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession,
) -> Candidate:
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.role_id == role_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    return candidate


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[CandidateOut], summary="List candidates for a role")
async def list_candidates(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    await _resolve_role(workspace_id, role_id, current_user, db)

    query = (
        select(Candidate)
        .where(Candidate.role_id == role_id)
        .order_by(Candidate.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        query = query.where(Candidate.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{candidate_id}", response_model=CandidateOut, summary="Get a single candidate")
async def get_candidate(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    await _resolve_role(workspace_id, role_id, current_user, db)
    return await _get_candidate_or_404(candidate_id, role_id, db)


@router.post(
    "/compare",
    summary="Side-by-side comparison of up to 5 candidates",
)
async def compare_candidates(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: CompareRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """
    Returns full candidate profiles + scores for side-by-side comparison.

    TODO: Add semantic similarity ranking against the role embedding.
    """
    if len(payload.candidate_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare more than 5 candidates at once.",
        )

    await _resolve_role(workspace_id, role_id, current_user, db)

    result = await db.execute(
        select(Candidate).where(
            Candidate.id.in_(payload.candidate_ids),
            Candidate.role_id == role_id,
        )
    )
    candidates = result.scalars().all()

    if len(candidates) != len(payload.candidate_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more candidates were not found for this role.",
        )

    return {"candidates": [CandidateOut.model_validate(c) for c in candidates]}


@router.post("/shortlist", summary="Mark a set of candidates as shortlisted")
async def shortlist_candidates(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: ShortlistRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Bulk-updates the status of the specified candidates to 'shortlisted'.

    TODO: Record a UsageEvent and enforce plan limits on shortlist exports.
    """
    await _resolve_role(workspace_id, role_id, current_user, db)

    result = await db.execute(
        select(Candidate).where(
            Candidate.id.in_(payload.candidate_ids),
            Candidate.role_id == role_id,
        )
    )
    candidates = result.scalars().all()

    updated_ids: list[str] = []
    for candidate in candidates:
        candidate.status = "shortlisted"
        updated_ids.append(str(candidate.id))

    await db.flush()
    return {"shortlisted": updated_ids, "count": len(updated_ids)}
