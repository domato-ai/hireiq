"""Stripe billing — checkout, webhook, portal, plan status."""
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

# Store Stripe customer IDs in memory (keyed by email)
_stripe_customers: dict[str, str] = {}  # email -> stripe_customer_id


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class PlanStatusResponse(BaseModel):
    plan: str
    email: str
    is_pro: bool


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
    # Return user from store, or create a minimal entry for valid tokens
    if email not in _users:
        return {"email": email, "plan": "free", "name": email.split("@")[0]}
    return _users.get(email)


def _get_or_create_customer(email: str) -> str:
    """Get existing Stripe customer or create one."""
    # Check memory cache
    if email in _stripe_customers:
        return _stripe_customers[email]

    # Search Stripe for existing customer
    existing = stripe_lib.Customer.list(email=email, limit=1)
    if existing.data:
        cust_id = existing.data[0].id
        _stripe_customers[email] = cust_id
        return cust_id

    # Create new customer
    customer = stripe_lib.Customer.create(email=email)
    _stripe_customers[email] = customer.id
    return customer.id


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

    # Already pro? Don't create another subscription
    if user.get("plan") == "pro":
        raise HTTPException(status_code=400, detail="You are already on the Pro plan")

    customer_id = _get_or_create_customer(email)

    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
            success_url="https://hireiq.domato.ai/?upgraded=true",
            cancel_url="https://hireiq.domato.ai/",
            metadata={"email": email},
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create checkout session.") from exc

    return CheckoutResponse(url=session.url or "")


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    authorization: str | None = Header(default=None),
):
    """Create a Stripe Customer Portal session to manage subscription."""
    _init_stripe()

    user = _get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to manage subscription")

    email = user["email"]

    # Find customer
    if email not in _stripe_customers:
        existing = stripe_lib.Customer.list(email=email, limit=1)
        if existing.data:
            _stripe_customers[email] = existing.data[0].id
        else:
            raise HTTPException(status_code=400, detail="No subscription found for this account")

    customer_id = _stripe_customers[email]

    try:
        portal = stripe_lib.billing_portal.Session.create(
            customer=customer_id,
            return_url="https://hireiq.domato.ai/",
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe portal error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to open subscription management.") from exc

    return PortalResponse(url=portal.url)


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
        email = (data.get("metadata") or {}).get("email") or data.get("customer_email", "")
        customer_id = data.get("customer", "")
        if email:
            email = email.lower().strip()
            if customer_id:
                _stripe_customers[email] = customer_id
            if email in _users:
                _users[email]["plan"] = "pro"
            else:
                _users[email] = {
                    "email": email, "name": email.split("@")[0],
                    "password_hash": "", "plan": "pro", "created_at": 0,
                }
            logger.info("Upgraded %s to pro (customer: %s)", email, customer_id)

    elif event_type == "customer.subscription.deleted":
        # Find email from customer ID
        customer_id = data.get("customer", "")
        email = ""
        for e, cid in _stripe_customers.items():
            if cid == customer_id:
                email = e
                break
        if not email:
            # Try metadata
            email = (data.get("metadata") or {}).get("email", "")
        if email and email in _users:
            _users[email]["plan"] = "free"
            logger.info("Downgraded %s to free (subscription cancelled)", email)

    return {"received": "ok"}


@router.get("/plan", response_model=PlanStatusResponse)
async def get_plan(
    authorization: str | None = Header(default=None),
):
    """Get current plan for the authenticated user."""
    user = _get_user_from_auth(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    plan = user.get("plan", "free")
    return PlanStatusResponse(plan=plan, email=user["email"], is_pro=plan == "pro")
