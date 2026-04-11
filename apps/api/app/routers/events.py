"""Funnel event tracking — lightweight analytics endpoint."""
from __future__ import annotations
import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.database import get_session_factory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


class EventBody(BaseModel):
    event: str
    session_id: str | None = None
    ref: str | None = None
    url: str | None = None


@router.post("", status_code=204)
async def track_event(body: EventBody, request: Request):
    """Record a funnel event. Fire-and-forget from the client."""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else None
    )
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(
                text("""
                    INSERT INTO funnel_events (event, session_id, ref, url, ip, created_at)
                    VALUES (:event, :session_id, :ref, :url, :ip, NOW())
                """),
                {
                    "event": body.event[:100],
                    "session_id": body.session_id,
                    "ref": body.ref,
                    "url": body.url,
                    "ip": ip,
                },
            )
            await session.commit()
    except Exception as e:
        logger.warning("Failed to record event: %s", e)
    return None
