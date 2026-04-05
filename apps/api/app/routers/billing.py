"""Stripe billing — checkout, webhook, plan status."""
from __future__ import annotations

import logging
from typing import Any

import stripe as stripe_lib
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.config import get_settings
from app.routers.auth import verify_token, _users

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CheckoutResponse(BaseModel):
    url: str


class PlanStatusResponse(BaseModel):
    plan: str
    email: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_stripe():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    stripe_lib.api_key = settings.stripe_secret_key


def _get_user_from_auth(authorization: str | None) -> dict | None:
    """Extract user from auth header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = verify_token(authorization[7:])
    if not payload:
        return None
    email = payload.get("email", "")
    return _users.get(email)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    authorization: str | None = Header(default=None),
):
    """Create a Stripe Checkout session for Pro upgrade."""
    _init_stripe()
    settings = get_settings()

    user = _get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to upgrade")

    email = user["email"]

    # Use the SWA URL for now — will switch to hireiq.domato.ai when domain is set up
    base_url = "https://kind-tree-0d675b200.6.azurestaticapps.net"

    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
            success_url=f"{base_url}/?upgraded=true",
            cancel_url=f"{base_url}/",
            customer_email=email,
            metadata={"email": email},
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create checkout session.") from exc

    return CheckoutResponse(url=session.url or "")


@router.post("/webhook", status_code=200, include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
):
    """Handle Stripe webhook events."""
    _init_stripe()
    settings = get_settings()

    body = await request.body()

    if not stripe_signature or not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Missing signature or webhook secret.")

    try:
        event = stripe_lib.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except stripe_lib.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature.")

    event_type = event["type"]
    data = event["data"]["object"]
    logger.info("Stripe event: %s", event_type)

    if event_type == "checkout.session.completed":
        # User completed payment — upgrade to pro
        email = data.get("metadata", {}).get("email") or data.get("customer_email", "")
        if email:
            email = email.lower().strip()
            if email in _users:
                _users[email]["plan"] = "pro"
                logger.info("Upgraded %s to pro", email)
            else:
                # User paid but not in memory — create entry so they get pro on next login
                _users[email] = {
                    "email": email,
                    "name": email.split("@")[0],
                    "password_hash": "",
                    "plan": "pro",
                    "created_at": 0,
                }
                logger.info("Created pro user for %s (from webhook)", email)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — downgrade to free
        email = data.get("metadata", {}).get("email", "")
        if email and email in _users:
            _users[email]["plan"] = "free"
            logger.info("Downgraded %s to free", email)

    return {"received": "ok"}


@router.get("/plan", response_model=PlanStatusResponse)
async def get_plan(
    authorization: str | None = Header(default=None),
):
    """Get current plan for the authenticated user."""
    user = _get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return PlanStatusResponse(plan=user.get("plan", "free"), email=user["email"])
