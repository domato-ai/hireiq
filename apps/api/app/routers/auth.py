from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.middleware.auth import CurrentUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None
    plan: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/login", summary="Redirect to Azure Entra ID login page")
async def login(
    settings: Annotated[Settings, Depends(get_settings)],
    redirect_uri: str | None = None,
) -> RedirectResponse:
    """
    Initiates the OAuth 2.0 / OIDC authorization code flow against
    Azure Entra ID. The client is redirected to Microsoft's login page.

    TODO: Build the MSAL authorization URL and redirect.
    """
    # Placeholder: in production build the MSAL URL and redirect.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Azure Entra ID login not yet configured.",
    )


@router.get("/callback", summary="OAuth callback — exchange code for tokens")
async def callback(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> TokenResponse:
    """
    Handles the authorization code callback from Azure Entra ID.
    Exchanges the code for an access + ID token, upserts the user in
    the database, and issues a signed application JWT.

    TODO: Implement MSAL token exchange and user upsert.
    """
    if error:
        logger.warning("Auth callback error: %s — %s", error, error_description)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_description or error,
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth callback not yet implemented.",
    )


@router.post("/logout", summary="Invalidate the current session / token")
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Logs out the authenticated user.

    For stateless JWT flows this is a client-side operation; for
    server-side session strategies, invalidate the session here.

    TODO: Add token blocklist / session invalidation if needed.
    """
    return {"detail": "Logged out successfully."}


@router.get("/me", response_model=UserOut, summary="Return the authenticated user's profile")
async def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Any:
    """Returns the profile of the currently authenticated user."""
    return current_user
