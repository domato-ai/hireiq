from __future__ import annotations

"""
Authentication middleware and FastAPI dependency.

In **development mode** (when ``AZURE_AD_TENANT_ID`` is empty/unset) the
dependency short-circuits entirely and returns a fixed mock ``User`` without
touching the database or validating any token.  This lets you run the API
locally without an Entra ID tenant.

In **production mode** (``AZURE_AD_TENANT_ID`` is set) the dependency
validates Azure Entra ID (formerly Azure AD) JWT tokens presented in the
``Authorization: Bearer <token>`` header:

  1. Decode the JWT header to obtain the ``kid`` (key ID).
  2. Fetch the JWKS from the Entra ID discovery endpoint (cached).
  3. Verify the signature, issuer (``iss``), audience (``aud``), and expiry.
  4. Load or upsert the corresponding ``User`` record from the database.

The ``get_current_user`` dependency is a thin wrapper suitable for injection
into any route that requires authentication.
"""

import logging
import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security scheme
# ---------------------------------------------------------------------------
# auto_error=False so that routes protected by get_current_user do not
# immediately 401 when no Authorization header is sent — the dependency
# itself decides what to do (e.g. return a mock user in dev mode).

_bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Type alias used by routers
# ---------------------------------------------------------------------------

CurrentUser = User

# ---------------------------------------------------------------------------
# Development mock user
# ---------------------------------------------------------------------------

_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

_dev_user_instance: User | None = None


def _make_dev_user() -> User:
    """
    Return a singleton transient ``User`` instance used in development mode.

    The instance is intentionally *not* attached to any SQLAlchemy session so
    it never touches the database.  It is safe to return from a FastAPI
    dependency because the ORM detects that it is transient and will not try
    to lazy-load any relationships.
    """
    global _dev_user_instance
    if _dev_user_instance is None:
        user = User.__new__(User)
        # Manually set all columns to avoid touching a session / DB.
        user.id = _DEV_USER_ID
        user.email = "dev@hireiq.local"
        user.name = "Dev User"
        user.entra_id = "dev-entra-id"
        user.plan = "pro"
        _dev_user_instance = user
    return _dev_user_instance


# ---------------------------------------------------------------------------
# JWKS cache (module-level, refreshed on unknown kid)
# ---------------------------------------------------------------------------

_jwks_cache: dict[str, dict] = {}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5), reraise=True)
async def _fetch_jwks(settings: Settings) -> dict:
    """
    Fetch the public key set from Azure Entra ID's OIDC discovery endpoint.

    The result is cached module-globally and refreshed only when a token is
    presented with an unknown ``kid``.
    """
    tenant_id = settings.azure_ad_tenant_id
    discovery_url = (
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]


async def _get_signing_key(kid: str, settings: Settings) -> dict:
    """Return the JWK for ``kid``, refreshing the cache if necessary."""
    if kid not in _jwks_cache:
        jwks = await _fetch_jwks(settings)
        _jwks_cache.clear()
        for key in jwks.get("keys", []):
            _jwks_cache[key["kid"]] = key

    if kid not in _jwks_cache:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to locate signing key for the provided token.",
        )
    return _jwks_cache[kid]


# ---------------------------------------------------------------------------
# Core verification logic (production only)
# ---------------------------------------------------------------------------


async def _verify_token(token: str, settings: Settings) -> dict:
    """
    Decode and verify an Entra ID JWT.

    Returns the decoded claims dict if valid.

    Raises:
        HTTPException 401 — on any verification failure.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid", "")
        signing_key = await _get_signing_key(kid, settings)

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.azure_ad_client_id,
            issuer=(
                f"https://login.microsoftonline.com/"
                f"{settings.azure_ad_tenant_id}/v2.0"
            ),
        )
        return claims  # type: ignore[return-value]

    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# User upsert (production only)
# ---------------------------------------------------------------------------


async def _get_or_create_user(claims: dict, db: AsyncSession) -> User:
    """
    Load the user matching the Entra ID OID claim, creating them if new.

    Args:
        claims: Decoded JWT payload from Entra ID.
        db: Async database session.

    Returns:
        The corresponding ``User`` ORM instance.
    """
    entra_id: str = claims.get("oid", "")
    email: str = claims.get("preferred_username") or claims.get("email") or ""
    name: str = claims.get("name") or ""

    result = await db.execute(select(User).where(User.entra_id == entra_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, name=name, entra_id=entra_id, plan="free")
        db.add(user)
        await db.flush()
        logger.info("Created new user: email=%s entra_id=%s", email, entra_id)
    else:
        user.email = email or user.email
        user.name = name or user.name

    return user


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """
    FastAPI dependency that returns the authenticated ``User`` instance.

    **Development mode** (``AZURE_AD_TENANT_ID`` is empty/unset):
        Returns a fixed mock user (id, email, name, plan="pro") without
        touching the database or requiring an ``Authorization`` header.
        A warning is logged on every request as a reminder.

    **Production mode** (``AZURE_AD_TENANT_ID`` is set):
        Validates the ``Authorization: Bearer <token>`` header against
        Azure Entra ID and upserts the matching ``User`` row.

    Usage::

        @router.get("/me")
        async def me(user: Annotated[User, Depends(get_current_user)]):
            return user

    Raises:
        HTTPException 401 — (production only) if the token is missing,
            invalid, or expired.
    """
    # ------------------------------------------------------------------
    # Development bypass — no Entra ID tenant configured
    # ------------------------------------------------------------------
    if not settings.azure_ad_tenant_id:
        logger.warning(
            "DEV MODE: AZURE_AD_TENANT_ID is not set. "
            "Returning mock user (dev@hireiq.local, plan=pro). "
            "Never run with this configuration in production."
        )
        return _make_dev_user()

    # ------------------------------------------------------------------
    # Production — require a valid bearer token
    # ------------------------------------------------------------------
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = await _verify_token(credentials.credentials, settings)
    user = await _get_or_create_user(claims, db)
    return user
