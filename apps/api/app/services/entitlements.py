from __future__ import annotations

"""
Plan entitlement service.

Defines per-plan limits and provides async helpers to check whether a user
or workspace has exceeded their quota. Used by router-level dependencies to
enforce gates before write operations.

Plan tiers:
  free  — limited workspaces, roles, and candidates per role
  pro   — higher limits, access to scoring and exports
  team  — unlimited or very high limits, SSO, audit log
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.role import Role
from app.models.workspace import Workspace

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanLimits:
    max_workspaces: int                  # -1 = unlimited
    max_roles_per_workspace: int
    max_candidates_per_role: int
    can_export_shortlist: bool
    can_compare_candidates: bool
    can_use_scoring: bool
    can_use_semantic_search: bool


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(
        max_workspaces=1,
        max_roles_per_workspace=3,
        max_candidates_per_role=10,
        can_export_shortlist=False,
        can_compare_candidates=False,
        can_use_scoring=False,
        can_use_semantic_search=False,
    ),
    "pro": PlanLimits(
        max_workspaces=5,
        max_roles_per_workspace=20,
        max_candidates_per_role=200,
        can_export_shortlist=True,
        can_compare_candidates=True,
        can_use_scoring=True,
        can_use_semantic_search=True,
    ),
    "team": PlanLimits(
        max_workspaces=-1,
        max_roles_per_workspace=-1,
        max_candidates_per_role=-1,
        can_export_shortlist=True,
        can_compare_candidates=True,
        can_use_scoring=True,
        can_use_semantic_search=True,
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_limits(plan: str) -> PlanLimits:
    """Return the PlanLimits for the given plan slug, defaulting to 'free'."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


# ---------------------------------------------------------------------------
# Quota checks
# ---------------------------------------------------------------------------


async def check_workspace_quota(user_id: uuid.UUID, plan: str, db: AsyncSession) -> None:
    """
    Raise ``EntitlementError`` if the user has reached their workspace limit.

    Args:
        user_id: UUID of the user creating the workspace.
        plan: Current plan slug.
        db: Async database session.

    Raises:
        EntitlementError: If the workspace quota is exceeded.
    """
    limits = get_limits(plan)
    if limits.max_workspaces == -1:
        return

    result = await db.execute(
        select(func.count()).select_from(Workspace).where(Workspace.owner_id == user_id)
    )
    count: int = result.scalar_one()

    if count >= limits.max_workspaces:
        raise EntitlementError(
            f"Your {plan!r} plan allows a maximum of {limits.max_workspaces} workspace(s). "
            "Please upgrade to create more workspaces."
        )


async def check_role_quota(
    workspace_id: uuid.UUID,
    plan: str,
    db: AsyncSession,
) -> None:
    """
    Raise ``EntitlementError`` if the workspace has reached its role limit.

    Args:
        workspace_id: UUID of the workspace.
        plan: Current plan slug.
        db: Async database session.

    Raises:
        EntitlementError: If the role quota is exceeded.
    """
    limits = get_limits(plan)
    if limits.max_roles_per_workspace == -1:
        return

    result = await db.execute(
        select(func.count()).select_from(Role).where(Role.workspace_id == workspace_id)
    )
    count: int = result.scalar_one()

    if count >= limits.max_roles_per_workspace:
        raise EntitlementError(
            f"Your {plan!r} plan allows a maximum of {limits.max_roles_per_workspace} role(s) "
            "per workspace. Please upgrade to add more roles."
        )


async def check_candidate_quota(
    role_id: uuid.UUID,
    plan: str,
    db: AsyncSession,
) -> None:
    """
    Raise ``EntitlementError`` if the role has reached its candidate limit.

    Args:
        role_id: UUID of the role.
        plan: Current plan slug.
        db: Async database session.

    Raises:
        EntitlementError: If the candidate quota is exceeded.
    """
    limits = get_limits(plan)
    if limits.max_candidates_per_role == -1:
        return

    result = await db.execute(
        select(func.count()).select_from(Candidate).where(Candidate.role_id == role_id)
    )
    count: int = result.scalar_one()

    if count >= limits.max_candidates_per_role:
        raise EntitlementError(
            f"Your {plan!r} plan allows a maximum of {limits.max_candidates_per_role} candidate(s) "
            "per role. Please upgrade to add more candidates."
        )


def require_feature(plan: str, feature: str) -> None:
    """
    Raise ``EntitlementError`` if the plan does not include ``feature``.

    Args:
        plan: Current plan slug.
        feature: Attribute name on ``PlanLimits`` (e.g. ``can_use_scoring``).

    Raises:
        EntitlementError: If the feature is not available on this plan.
    """
    limits = get_limits(plan)
    if not getattr(limits, feature, False):
        human_name = feature.replace("can_", "").replace("_", " ")
        raise EntitlementError(
            f"The {human_name!r} feature is not available on your {plan!r} plan. "
            "Please upgrade to access it."
        )


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class EntitlementError(Exception):
    """Raised when a plan quota or feature gate is exceeded."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
