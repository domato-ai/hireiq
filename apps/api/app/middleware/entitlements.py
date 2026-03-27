from __future__ import annotations

"""
Entitlement enforcement middleware / FastAPI dependencies.

Provides ``Depends``-compatible callables that check plan quotas before
allowing write operations to proceed. They are thin wrappers around the
service-layer quota functions in ``app.services.entitlements``.

Usage in a router::

    @router.post("/workspaces", dependencies=[Depends(require_workspace_quota)])
    async def create_workspace(...): ...
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.database import AsyncSession, get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.services.entitlements import (
    EntitlementError,
    check_candidate_quota,
    check_role_quota,
    check_workspace_quota,
    require_feature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entitlement_http_error(exc: EntitlementError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=exc.message,
    )


# ---------------------------------------------------------------------------
# Quota dependencies
# ---------------------------------------------------------------------------


async def require_workspace_quota(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Dependency that blocks workspace creation if the user's plan limit is reached.

    Raises:
        HTTPException 402 — if workspace quota is exceeded.
    """
    try:
        await check_workspace_quota(current_user.id, current_user.plan, db)
    except EntitlementError as exc:
        raise _entitlement_http_error(exc) from exc


async def require_role_quota(
    workspace_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Dependency that blocks role creation if the workspace's plan limit is reached.

    ``workspace_id`` is resolved from the path parameter automatically by FastAPI.

    Raises:
        HTTPException 402 — if role quota is exceeded.
    """
    try:
        await check_role_quota(workspace_id, current_user.plan, db)
    except EntitlementError as exc:
        raise _entitlement_http_error(exc) from exc


async def require_candidate_quota(
    role_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Dependency that blocks candidate uploads if the role's plan limit is reached.

    Raises:
        HTTPException 402 — if candidate quota is exceeded.
    """
    try:
        await check_candidate_quota(role_id, current_user.plan, db)
    except EntitlementError as exc:
        raise _entitlement_http_error(exc) from exc


# ---------------------------------------------------------------------------
# Feature flag dependencies
# ---------------------------------------------------------------------------


def _make_feature_dep(feature: str):
    """Factory that returns a dependency function for a feature flag check."""

    async def _dep(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> None:
        try:
            require_feature(current_user.plan, feature)
        except EntitlementError as exc:
            raise _entitlement_http_error(exc) from exc

    _dep.__name__ = f"require_{feature}"
    return _dep


require_scoring = _make_feature_dep("can_use_scoring")
require_semantic_search = _make_feature_dep("can_use_semantic_search")
require_compare = _make_feature_dep("can_compare_candidates")
require_export = _make_feature_dep("can_export_shortlist")
