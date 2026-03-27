from __future__ import annotations

import logging
from typing import Annotated, Any

import stripe as stripe_lib
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.middleware.auth import CurrentUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PlanStatus(BaseModel):
    plan: str
    status: str
    current_period_end: str | None
    stripe_customer_id: str | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_stripe(settings: Settings) -> None:
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured.",
        )
    stripe_lib.api_key = settings.stripe_secret_key


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create a Stripe Checkout session for upgrading the plan",
)
async def create_checkout_session(
    payload: CheckoutRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Any:
    """
    Creates a Stripe Checkout session for the authenticated user.

    TODO: Retrieve or create a Stripe customer and attach to the session.
    """
    _get_stripe(settings)

    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": payload.price_id, "quantity": 1}],
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            client_reference_id=str(current_user.id),
            metadata={"user_id": str(current_user.id)},
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create Stripe Checkout session.",
        ) from exc

    return CheckoutResponse(checkout_url=session.url or "")


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhook events",
    include_in_schema=False,  # Do not expose in OpenAPI docs
)
async def stripe_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
) -> dict[str, str]:
    """
    Verifies and processes incoming Stripe webhook events.

    Supported events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_failed

    TODO: Implement full event handling and database updates.
    """
    _get_stripe(settings)

    body = await request.body()

    if not stripe_signature or not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature or webhook secret.",
        )

    try:
        event = stripe_lib.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except stripe_lib.errors.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature."
        ) from exc

    event_type: str = event["type"]
    logger.info("Received Stripe event: %s", event_type)

    # Route event types to handlers
    handlers: dict[str, Any] = {
        "customer.subscription.created": _handle_subscription_created,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
        "invoice.payment_failed": _handle_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(event["data"]["object"])

    return {"received": "ok"}


@router.get(
    "/plan",
    response_model=PlanStatus,
    summary="Get the current user's active plan and subscription status",
)
async def get_plan_status(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Any:
    """
    Returns the current plan status for the authenticated user.

    TODO: Enrich with live Stripe data if needed.
    """
    subscription = getattr(current_user, "subscription", None)
    return PlanStatus(
        plan=current_user.plan,
        status=subscription.status if subscription else "active",
        current_period_end=(
            subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
        ),
        stripe_customer_id=subscription.stripe_customer_id if subscription else None,
    )


@router.post(
    "/portal",
    summary="Create a Stripe Customer Portal session for managing subscription",
)
async def create_portal_session(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    return_url: str = "http://localhost:3000/settings/billing",
) -> dict[str, str]:
    """
    Opens the Stripe Customer Portal so the user can manage their subscription,
    update payment methods, and download invoices.
    """
    _get_stripe(settings)

    subscription = getattr(current_user, "subscription", None)
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer found for this account.",
        )

    try:
        portal = stripe_lib.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url,
        )
    except stripe_lib.StripeError as exc:
        logger.error("Stripe portal error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create Stripe portal session.",
        ) from exc

    return {"portal_url": portal.url}


# ---------------------------------------------------------------------------
# Private webhook event handlers (stubs)
# ---------------------------------------------------------------------------


async def _handle_subscription_created(data: dict[str, Any]) -> None:
    """TODO: Create/update Subscription record and set user plan."""
    logger.info("Subscription created: %s", data.get("id"))


async def _handle_subscription_updated(data: dict[str, Any]) -> None:
    """TODO: Update Subscription record status and current_period_end."""
    logger.info("Subscription updated: %s", data.get("id"))


async def _handle_subscription_deleted(data: dict[str, Any]) -> None:
    """TODO: Mark subscription as canceled and downgrade user to free tier."""
    logger.info("Subscription deleted: %s", data.get("id"))


async def _handle_payment_failed(data: dict[str, Any]) -> None:
    """TODO: Notify user of failed payment and update subscription status."""
    logger.info("Payment failed for invoice: %s", data.get("id"))
