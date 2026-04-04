"""Contact form endpoint — receives messages and forwards to support@domato.ai."""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])

# In-memory store of messages (fallback when email isn't configured)
_messages: list[dict] = []


class ContactRequest(BaseModel):
    name: str = ""
    email: str
    message: str


class ContactResponse(BaseModel):
    status: str
    detail: str


@router.post("", response_model=ContactResponse, status_code=200)
async def submit_contact(body: ContactRequest):
    """Receive a contact form submission."""
    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=400, detail="Valid email is required")

    if not body.message or len(body.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Message must be at least 10 characters")

    timestamp = datetime.now(timezone.utc).isoformat()

    # Store the message
    _messages.append({
        "name": body.name,
        "email": body.email,
        "message": body.message,
        "timestamp": timestamp,
    })

    logger.info(
        "Contact form submission from %s <%s>: %s",
        body.name or "Anonymous",
        body.email,
        body.message[:100],
    )

    # Send email
    settings = get_settings()

    if settings.smtp_host:
        try:
            msg = MIMEText(
                f"From: {body.name or 'Anonymous'} <{body.email}>\n"
                f"Time: {timestamp}\n\n"
                f"{body.message}"
            )
            msg["Subject"] = f"[HireIQ Contact] {body.name or body.email}"
            msg["From"] = settings.smtp_from
            msg["To"] = settings.smtp_to
            msg["Reply-To"] = body.email

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_pass:
                    server.login(settings.smtp_user, settings.smtp_pass)
                server.send_message(msg)

            logger.info("Contact email sent to %s", settings.smtp_to)
        except Exception as e:
            logger.warning("Failed to send contact email: %s (message still stored)", e)
    else:
        logger.info("SMTP not configured — message stored in memory. Set SMTP_HOST to enable.")

    return ContactResponse(
        status="sent",
        detail="Your message has been received. We'll get back to you shortly.",
    )
