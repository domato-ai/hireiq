"""DB-backed usage tracking. Tracks analyses per user/IP per month."""
from __future__ import annotations
import logging
import uuid as uuid_mod
from datetime import datetime, timezone

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session_factory
from app.models.usage_event import UsageEvent
from app.models.user import User

logger = logging.getLogger(__name__)

# Limits per plan
LIMITS = {
    "anonymous": {"analyses": 3, "resumes_per_analysis": 5},
    "free": {"analyses": 10, "resumes_per_analysis": 10},
    "pro": {"analyses": -1, "resumes_per_analysis": 50},  # -1 = unlimited
}

# Sentinel UUID for anonymous usage events
ANON_USER_ID = uuid_mod.UUID("00000000-0000-0000-0000-000000000000")


def _current_month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _event_type_for(identifier: str) -> str:
    """Consistent event_type key for an identifier."""
    if identifier.startswith("ip:"):
        return f"analysis:{identifier}"
    return f"analysis:{identifier}"


async def _count_analyses_this_month(identifier: str) -> int:
    """Count analysis events for an identifier this month."""
    month_start = _current_month_start()
    factory = get_session_factory()
    async with factory() as session:
        # For authenticated users, look up by email -> user_id
        if not identifier.startswith("ip:"):
            result = await session.execute(
                select(User.id).where(User.email == identifier)
            )
            user_id = result.scalar_one_or_none()
            if user_id:
                count_result = await session.execute(
                    select(func.count()).select_from(UsageEvent).where(
                        and_(
                            UsageEvent.user_id == user_id,
                            UsageEvent.event_type.like("analysis%"),
                            UsageEvent.created_at >= month_start,
                        )
                    )
                )
                return count_result.scalar() or 0

        # Anonymous / IP-based — count by event_type key
        evt_type = _event_type_for(identifier)
        count_result = await session.execute(
            select(func.count()).select_from(UsageEvent).where(
                and_(
                    UsageEvent.event_type == evt_type,
                    UsageEvent.created_at >= month_start,
                )
            )
        )
        return count_result.scalar() or 0


async def check_quota_async(identifier: str, plan: str = "anonymous") -> dict:
    """Check if user has remaining quota. Returns usage info."""
    used = await _count_analyses_this_month(identifier)
    limit_info = LIMITS.get(plan, LIMITS["anonymous"])
    max_analyses = limit_info["analyses"]

    return {
        "allowed": max_analyses == -1 or used < max_analyses,
        "used": used,
        "limit": max_analyses,
        "remaining": max_analyses - used if max_analyses != -1 else -1,
        "plan": plan,
        "resumes_per_analysis": limit_info["resumes_per_analysis"],
        "resets_at": _current_month_start().isoformat().replace("+00:00", "Z"),
    }


async def record_usage_async(identifier: str, user_id=None):
    """Record one analysis usage event to the database."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            if not identifier.startswith("ip:") and not user_id:
                # Try to resolve user_id from email
                result = await session.execute(
                    select(User.id).where(User.email == identifier)
                )
                user_id = result.scalar_one_or_none()

            if not user_id:
                # Ensure anonymous sentinel user exists
                result = await session.execute(
                    select(User.id).where(User.id == ANON_USER_ID)
                )
                if not result.scalar_one_or_none():
                    anon_user = User(
                        id=ANON_USER_ID,
                        email="anonymous@hireiq.system",
                        name="Anonymous",
                        plan="anonymous",
                    )
                    session.add(anon_user)
                    await session.flush()
                user_id = ANON_USER_ID

            evt_type = _event_type_for(identifier)
            event = UsageEvent(
                user_id=user_id,
                event_type=evt_type,
                quantity=1,
            )
            session.add(event)
            await session.commit()
            logger.info("Usage recorded for %s (event_type=%s)", identifier, evt_type)
    except Exception as e:
        logger.error("Failed to record usage for %s: %s", identifier, e)
