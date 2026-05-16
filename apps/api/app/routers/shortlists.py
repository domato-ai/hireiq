"""Shared shortlist endpoints — save and retrieve analysis results via short link."""
from __future__ import annotations
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.database import get_session_factory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shortlists", tags=["shortlists"])


class SaveShortlistRequest(BaseModel):
    analysis: dict


class SaveShortlistResponse(BaseModel):
    id: str
    url: str


@router.post("", response_model=SaveShortlistResponse, status_code=201)
async def save_shortlist(body: SaveShortlistRequest, request: Request):
    """Save an analysis result and return a shareable short ID."""
    short_id = uuid.uuid4().hex[:8]
    import json

    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(
                text("""
                    INSERT INTO shared_shortlists (id, analysis_json, created_by, created_at, expires_at)
                    VALUES (:id, cast(:json as jsonb), :ip, NOW(), NOW() + interval '30 days')
                """),
                {
                    "id": short_id,
                    "json": json.dumps(body.analysis),
                    "ip": request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                        or (request.client.host if request.client else None),
                },
            )
            await session.commit()
    except Exception as e:
        logger.error("Failed to save shortlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save shortlist")

    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "hireiq.domato.ai"
    scheme = request.headers.get("x-forwarded-proto") or "https"
    url = f"{scheme}://{host}/s?id={short_id}"

    return SaveShortlistResponse(id=short_id, url=url)


@router.get("/{shortlist_id}")
async def get_shortlist(shortlist_id: str):
    """Retrieve a shared shortlist by ID."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                text("SELECT analysis_json, created_at, expires_at FROM shared_shortlists WHERE id = :id"),
                {"id": shortlist_id},
            )
            row = result.first()
    except Exception as e:
        logger.error("Failed to get shortlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve shortlist")

    if not row:
        raise HTTPException(status_code=404, detail="Shortlist not found or expired")

    return {
        "id": shortlist_id,
        "analysis": row[0],
        "created_at": row[1].isoformat() if row[1] else None,
        "expires_at": row[2].isoformat() if row[2] else None,
    }
