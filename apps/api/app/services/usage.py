"""In-memory usage tracking. Tracks analyses per user/IP per month."""
from __future__ import annotations
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Limits per plan
LIMITS = {
    "anonymous": {"analyses": 3, "resumes_per_analysis": 5},
    "free": {"analyses": 10, "resumes_per_analysis": 10},
    "pro": {"analyses": -1, "resumes_per_analysis": 50},  # -1 = unlimited
}

# In-memory store: {identifier: {"count": int, "month": "YYYY-MM"}}
_usage: dict[str, dict] = {}


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_usage(identifier: str) -> dict:
    month = _current_month()
    entry = _usage.get(identifier)
    if not entry or entry.get("month") != month:
        _usage[identifier] = {"count": 0, "month": month}
    return _usage[identifier]


def check_quota(identifier: str, plan: str = "anonymous") -> dict:
    """Check if user has remaining quota. Returns usage info."""
    entry = _get_usage(identifier)
    limit = LIMITS.get(plan, LIMITS["anonymous"])
    max_analyses = limit["analyses"]
    used = entry["count"]

    return {
        "allowed": max_analyses == -1 or used < max_analyses,
        "used": used,
        "limit": max_analyses,
        "remaining": max_analyses - used if max_analyses != -1 else -1,
        "plan": plan,
        "resumes_per_analysis": limit["resumes_per_analysis"],
        "resets_at": f"{_current_month()}-01T00:00:00Z",  # Approximate
    }


def record_usage(identifier: str):
    """Record one analysis usage."""
    entry = _get_usage(identifier)
    entry["count"] += 1
    logger.info("Usage recorded for %s: %d analyses this month", identifier, entry["count"])
