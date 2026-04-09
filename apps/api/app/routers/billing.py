"""Stripe billing — checkout, webhook, portal, plan status. DB-backed."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import stripe as stripe_lib
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.routers.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


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


async def _get_user_from_auth(authorization: str | None, db: AsyncSession) -> User | None:
    """Extract user from auth header, looking up from DB."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = verify_token(authorization[7:])
    if not payload:
        return None
    email = payload.get("email", "")
    if not email:
        return None
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        # Create a minimal user for valid tokens with no DB record
        user = User(email=email, name=email.split("@")[0], plan="free")
        db.add(user)
        await db.flush()
    return user


async def _get_or_create_stripe_customer(user: User, db: AsyncSession) -> str:
    """Get existing Stripe customer ID or create one."""
    # Check if user already has a stripe_customer_id
    if user.stripe_customer_id:
        return user.stripe_customer_id

    # Check subscription table too
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()
    if sub and sub.stripe_customer_id:
        user.stripe_customer_id = sub.stripe_customer_id
        return sub.stripe_customer_id

    # Search Stripe for existing customer
    existing = stripe_lib.Customer.list(email=user.email, limit=1)
    if existing.data:
        cust_id = existing.data[0].id
    else:
        customer = stripe_lib.Customer.create(email=user.email)
        cust_id = customer.id

    user.stripe_customer_id = cust_id
    return cust_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    authorization: str | None = Header(default=None),
    currency: str | None = Header(default=None, alias="x-currency"),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout session for Pro upgrade."""
    _init_stripe()
    settings = get_settings()

    user = await _get_user_from_auth(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to upgrade")

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="You are already on the Pro plan")

    customer_id = await _get_or_create_stripe_customer(user, db)

    # Pick price based on currency
    if currency and currency.lower() == "usd" and settings.stripe_price_id_pro_usd:
        price_id = settings.stripe_price_id_pro_usd
    else:
        price_id = settings.stripe_price_id_pro

    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://hireiq.domato.ai/?upgraded=true",
            cancel_url="https://hireiq.domato.ai/",
            metadata={"email": user.email},
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create checkout session.") from exc

    return CheckoutResponse(url=session.url or "")


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Customer Portal session to manage subscription."""
    _init_stripe()

    user = await _get_user_from_auth(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to manage subscription")

    if not user.stripe_customer_id:
        # Try to find from Stripe
        existing = stripe_lib.Customer.list(email=user.email, limit=1)
        if existing.data:
            user.stripe_customer_id = existing.data[0].id
        else:
            raise HTTPException(status_code=400, detail="No subscription found for this account")

    try:
        portal = stripe_lib.billing_portal.Session.create(
            customer=user.stripe_customer_id,
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
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events — persisted to DB."""
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
        subscription_id = data.get("subscription", "")

        if email:
            email = email.lower().strip()
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                user = User(email=email, name=email.split("@")[0], plan="pro")
                db.add(user)
                await db.flush()
            else:
                user.plan = "pro"

            if customer_id:
                user.stripe_customer_id = customer_id

            # Upsert subscription record
            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                sub.stripe_customer_id = customer_id
                sub.stripe_subscription_id = subscription_id
                sub.plan = "pro"
                sub.status = "active"
            else:
                sub = Subscription(
                    user_id=user.id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    plan="pro",
                    status="active",
                )
                db.add(sub)

            logger.info("Upgraded %s to pro (customer: %s)", email, customer_id)

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer", "")
        subscription_id = data.get("id", "")

        # Find user by stripe_customer_id
        user = None
        if customer_id:
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()

        if not user and customer_id:
            # Try via subscription table
            sub_result = await db.execute(
                select(Subscription).where(Subscription.stripe_customer_id == customer_id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                user_result = await db.execute(
                    select(User).where(User.id == sub.user_id)
                )
                user = user_result.scalar_one_or_none()

        if user:
            user.plan = "free"
            # Update subscription status
            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                sub.status = "canceled"
            logger.info("Downgraded %s to free (subscription cancelled)", user.email)

    return {"received": "ok"}


@router.get("/plan", response_model=PlanStatusResponse)
async def get_plan(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get current plan for the authenticated user."""
    user = await _get_user_from_auth(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return PlanStatusResponse(plan=user.plan, email=user.email, is_pro=user.plan == "pro")


class BillingStatusResponse(BaseModel):
    plan: str
    currentPeriodEnd: str | None = None
    candidatesUsed: int = 0
    candidatesLimit: int = 0
    rolesActive: int = 0
    rolesLimit: int = 0


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get full billing status for the frontend billing page."""
    user = await _get_user_from_auth(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get subscription period end if exists
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = sub_result.scalar_one_or_none()
    period_end = sub.current_period_end.isoformat() if sub and sub.current_period_end else None

    # Plan-based limits
    plan_limits = {
        "free": {"candidates": 10, "roles": 3},
        "pro": {"candidates": 500, "roles": 50},
        "team": {"candidates": 5000, "roles": 200},
    }
    limits = plan_limits.get(user.plan, plan_limits["free"])

    # Map internal plan names to frontend plan names
    plan_map = {"free": "starter", "pro": "growth", "team": "enterprise"}

    return BillingStatusResponse(
        plan=plan_map.get(user.plan, "starter"),
        currentPeriodEnd=period_end,
        candidatesUsed=0,  # TODO: count from usage_events
        candidatesLimit=limits["candidates"],
        rolesActive=0,  # TODO: count from roles table
        rolesLimit=limits["roles"],
    )


class PricingResponse(BaseModel):
    currency: str
    symbol: str
    pro_price: int
    pro_interval: str = "month"


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing(
    request: Request,
):
    """Return pricing based on user's geo location (from CF/Azure headers or IP)."""
    # Check common geo headers set by CDN/reverse proxy
    country = (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-azure-clientip-country")
        or request.headers.get("x-country")
        or ""
    ).upper()

    # USD countries
    usd_countries = {"US", "PR", "GU", "VI", "AS", "MP",  # US territories
                     "EC", "SV", "PA", "TL", "MH", "FM", "PW"}  # USD-pegged

    if country in usd_countries:
        return PricingResponse(currency="usd", symbol="$", pro_price=12)
    elif country in {"AU", ""}:
        # Default to AUD (empty = unknown, assume AU since we're AU-based)
        return PricingResponse(currency="aud", symbol="A$", pro_price=19)
    elif country in {"GB"}:
        return PricingResponse(currency="aud", symbol="A$", pro_price=19)  # TODO: add GBP price
    else:
        # International — show USD
        return PricingResponse(currency="usd", symbol="$", pro_price=12)
