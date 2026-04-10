"""
Outreach management — recruiter/HR contact CRUD, email campaigns, tracking.
All data persisted to PostgreSQL via SQLAlchemy.

Server-rendered HTML dashboard at /api/admin/outreach (cookie auth).

Endpoints:
  GET  /api/admin/outreach              Dashboard HTML
  POST /api/admin/outreach/login        Login form handler
  POST /api/admin/outreach/logout       Clear session
  GET  /api/admin/outreach/api/contacts List contacts (JSON)
  POST /api/admin/outreach/api/contacts Create/upsert contact
  PATCH /api/admin/outreach/api/contacts/{id}  Update contact
  DELETE /api/admin/outreach/api/contacts/{id} Delete contact
  POST /api/admin/outreach/api/send/{id}  Send to one contact
  POST /api/admin/outreach/api/send-batch Send batch
  POST /api/admin/outreach/api/import   Import CSV
  GET  /api/admin/outreach/api/stats    Stats
  GET  /api/admin/outreach/unsubscribe  Public unsubscribe
  GET  /r                               Click tracking (registered separately)
  GET  /o                               Open tracking (registered separately)
"""

import csv
import hashlib
import hmac as hmac_mod
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from urllib.parse import quote, unquote
import smtplib

from jose import jwt, JWTError
from fastapi import APIRouter, Cookie, Depends, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, get_session_factory
from app.models.outreach import OutreachContact, OutreachSendLog, OutreachClick
from app.services.recruiter_scraper import scrape_website_for_emails, scrape_rcsa_directory, google_search_agencies

logger = logging.getLogger(__name__)

settings = get_settings()

router = APIRouter(prefix="/api/admin/outreach", tags=["outreach"])
tracking_router = APIRouter(tags=["outreach-tracking"])

# ── Constants ────────────────────────────────────────────────────
_USER = "outreach manager"
_PASS = "Domato2025!"
_COOKIE = "hiq_outreach"
_EXP_H = 12
BACKEND_URL = "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io"
WEBSITE = "https://hireiq.domato.ai"
FROM_EMAIL = settings.smtp_from or "support@domato.ai"
FROM_NAME = "HireIQ"

INDUSTRIES = ["tech", "healthcare", "finance", "general", "agency"]
ROLE_TYPES = ["recruiter", "hr_manager", "talent_acquisition", "agency_director"]
STATUSES = ["not_started", "sent", "delivered", "bounced", "failed", "responded", "unsubscribed"]

# ── Auth ─────────────────────────────────────────────────────────

def _secret():
    return settings.secret_key or "outreach-dev-secret"


def _make_token() -> str:
    return jwt.encode(
        {"sub": _USER, "exp": datetime.now(timezone.utc) + timedelta(hours=_EXP_H)},
        _secret(), algorithm="HS256",
    )


def _verify(token: str | None) -> bool:
    if not token:
        return False
    try:
        p = jwt.decode(token, _secret(), algorithms=["HS256"])
        return p.get("sub") == _USER
    except (JWTError, Exception):
        return False


def _unauth():
    return HTMLResponse(_login_html(), status_code=200)


def _hmac_token(email: str) -> str:
    return hmac_mod.new(_secret().encode(), email.lower().encode(), hashlib.sha256).hexdigest()[:16]


# ── SMTP sending ─────────────────────────────────────────────────

def _send_email_smtp(to: str, subject: str, html_body: str) -> dict:
    """Send an email via SMTP. Returns {"ok": bool, "status": str, "error": str}."""
    if not settings.smtp_host or not settings.smtp_user:
        logger.warning("SMTP not configured — logging email instead")
        logger.info(f"Would send to {to}: {subject}")
        return {"ok": True, "status": "delivered", "error": ""}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)
        return {"ok": True, "status": "delivered", "error": ""}
    except smtplib.SMTPRecipientsRefused as e:
        return {"ok": False, "status": "bounced", "error": str(e)}
    except Exception as e:
        logger.error(f"SMTP send failed to {to}: {e}")
        return {"ok": False, "status": "failed", "error": str(e)}


# ── Tracked URLs ─────────────────────────────────────────────────

def _tracked_url(url: str, email: str) -> str:
    return f"{BACKEND_URL}/r?u={quote(url, safe='')}&e={quote(email, safe='')}"


def _open_pixel(email: str) -> str:
    return f'<img src="{BACKEND_URL}/o?e={quote(email, safe="")}" width="1" height="1" style="display:none" />'


def _unsubscribe_url(email: str) -> str:
    return f"{BACKEND_URL}/api/admin/outreach/unsubscribe?e={quote(email, safe='')}&t={_hmac_token(email)}"


# ── Email builder ────────────────────────────────────────────────

def _kpi_cell(icon: str, value: str, label: str) -> str:
    return (f'<td style="padding:14px;text-align:center;background:#161625;border-radius:8px;width:33%;border:1px solid #2a2a40;">'
            f'<div style="font-size:22px;margin-bottom:4px;">{icon}</div>'
            f'<div style="font-size:20px;font-weight:700;color:#e2e8f0;">{value}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:2px;text-transform:uppercase;letter-spacing:0.04em;">{label}</div></td>')


def _build_email_html(contact: dict) -> str:
    name = contact.get("contact_name") or "there"
    first = name.split()[0] if name != "there" else "there"
    company = contact.get("company_name") or "your team"
    industry = (contact.get("industry") or "general").lower()
    email = contact.get("email", "")

    # Industry-based hook
    hooks = {
        "tech": {
            "pain": "Screening 50 developer resumes for one role shouldn&rsquo;t take a full day",
            "detail": "Technical skills, frameworks, and years of experience buried across inconsistent CV formats &mdash; it adds up fast.",
        },
        "healthcare": {
            "pain": "Healthcare credentials and compliance checks buried across resumes",
            "detail": "Certifications, licensure, and specialisations scattered across 30+ applications &mdash; one missed detail can cost you.",
        },
        "finance": {
            "pain": "Regulatory experience and certifications scattered across 30+ CVs",
            "detail": "CFA, Series exams, compliance history &mdash; finding qualified candidates means reading every line of every resume.",
        },
        "agency": {
            "pain": "Your clients expect shortlists in hours, not days",
            "detail": "Multiple roles, multiple clients, hundreds of resumes. Manual screening kills your margins.",
        },
        "general": {
            "pain": "Still reading every resume top to bottom?",
            "detail": "When you&rsquo;re hiring for multiple roles, manual screening doesn&rsquo;t scale.",
        },
    }
    h = hooks.get(industry, hooks["general"])

    signup_url = _tracked_url(f"{WEBSITE}?ref=outreach", email)
    features_url = _tracked_url(WEBSITE, email)
    pricing_url = _tracked_url(WEBSITE, email)
    contact_url = _tracked_url(f"{WEBSITE}/contact", email)
    unsub_url = _unsubscribe_url(email)

    # KPI row
    kpi_row = '<table role="presentation" cellpadding="0" cellspacing="6" width="100%"><tr>'
    kpi_row += _kpi_cell("&#9889;", "30s", "Per Role")
    kpi_row += _kpi_cell("&#127919;", "8", "Score Factors")
    kpi_row += _kpi_cell("&#128202;", "100%", "Evidence-Backed")
    kpi_row += '</tr></table>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#0a0a0a;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#0a0a0a;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width:600px;width:100%;background-color:#111118;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.5);">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#0a0a14 0%,#12121f 50%,#1a1a30 100%);padding:28px 32px 20px;border-bottom:1px solid #2a2a40;">
<a href="{_tracked_url(WEBSITE, email)}" style="text-decoration:none;">
<span style="font-size:24px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;">Hire</span><span style="font-size:24px;font-weight:700;color:#7c5cff;letter-spacing:-0.02em;">IQ</span>
</a>
<p style="margin:8px 0 0;font-size:13px;color:#94a3b8;">Evidence-first hiring &bull; <strong style="color:#e2e8f0;">Rank candidates in seconds</strong></p>
</td></tr>

<!-- Greeting + Hook -->
<tr><td style="padding:28px 32px 12px;">
<p style="margin:0 0 14px;color:#e2e8f0;font-size:15px;font-weight:500;">Hi {first},</p>
<p style="margin:0 0 14px;color:#c4c4d4;font-size:14px;line-height:1.6;">I know {company} handles a lot of hiring. I wanted to show you something that could genuinely save your team hours every week.</p>
</td></tr>

<!-- Pain point callout -->
<tr><td style="padding:0 32px 16px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
<tr><td style="padding:14px 18px;background:#1a1528;border-left:4px solid #7c5cff;border-radius:0 8px 8px 0;">
<p style="margin:0;color:#c4b5fd;font-size:13px;line-height:1.5;font-style:italic;">{h["pain"]}</p>
<p style="margin:8px 0 0;color:#94a3b8;font-size:12px;line-height:1.5;">{h["detail"]}</p>
</td></tr>
</table>
</td></tr>

<!-- Solution intro -->
<tr><td style="padding:0 32px 8px;">
<p style="margin:0;color:#c4c4d4;font-size:14px;line-height:1.6;"><strong style="color:#e2e8f0;">HireIQ ranks candidates against your job description in 30 seconds.</strong> Paste a JD, drop resumes, get an evidence-backed shortlist.</p>
</td></tr>

<!-- Feature grid (2x3) -->
<tr><td style="padding:8px 32px;">
<table role="presentation" cellpadding="0" cellspacing="8" width="100%">
<tr>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#128203;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">Paste any JD</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">Instant criteria extraction &mdash; skills, experience, qualifications auto-detected.</div>
</td>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#128196;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">Drop Resumes</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">AI reads every line of every CV &mdash; PDF, DOCX, any format.</div>
</td>
</tr>
<tr>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#127919;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">8-Factor Scoring</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">Evidence for every match &mdash; no black-box rankings.</div>
</td>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#9878;&#65039;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">Side-by-Side Compare</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">Compare candidates head-to-head. Decide faster.</div>
</td>
</tr>
<tr>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#128269;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">Skills Gap Analysis</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">Know exactly what each candidate is missing before the interview.</div>
</td>
<td style="width:50%;padding:14px;background:#13132a;border-radius:8px;border:1px solid #2a2a45;vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">&#10024;</div>
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;">Recruiter Summary</div>
<div style="font-size:12px;color:#94a3b8;line-height:1.4;">AI-generated candidate brief &mdash; save hours per role.</div>
</td>
</tr>
</table>
</td></tr>

<!-- KPI row -->
<tr><td style="padding:12px 32px 4px;">{kpi_row}</td></tr>

<!-- CTA block -->
<tr><td style="padding:16px 32px 8px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:linear-gradient(135deg,#1a1040 0%,#251650 100%);border-radius:10px;overflow:hidden;border:1px solid #3a2a60;">
<tr><td style="padding:24px;text-align:center;">
<p style="margin:0 0 6px;color:#ffffff;font-size:16px;font-weight:700;">Stop screening. Start shortlisting.</p>
<p style="margin:0 0 16px;color:#94a3b8;font-size:13px;">Rank every candidate against your JD &mdash; free to start.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
<a href="{signup_url}" style="display:inline-block;background:#7c5cff;color:#ffffff;font-size:14px;font-weight:700;padding:14px 32px;border-radius:8px;text-decoration:none;">Try HireIQ Free &rarr;</a>
</td></tr></table>
<p style="margin:10px 0 0;color:#64748b;font-size:11px;">No credit card &bull; Unlimited JDs &bull; Free tier included</p>
</td></tr>
</table>
</td></tr>

<!-- Secondary actions -->
<tr><td style="padding:8px 32px;">
<table role="presentation" cellpadding="0" cellspacing="8" width="100%"><tr>
<td style="width:50%;text-align:center;background:#161625;border-radius:8px;padding:14px 12px;border:1px solid #2a2a40;">
<a href="{features_url}" style="text-decoration:none;">
<span style="display:block;font-size:18px;margin-bottom:4px;">&#128218;</span>
<span style="font-size:12px;font-weight:600;color:#e2e8f0;">Features</span>
</a>
</td>
<td style="width:50%;text-align:center;background:#161625;border-radius:8px;padding:14px 12px;border:1px solid #2a2a40;">
<a href="{pricing_url}" style="text-decoration:none;">
<span style="display:block;font-size:18px;margin-bottom:4px;">&#128179;</span>
<span style="font-size:12px;font-weight:600;color:#e2e8f0;">Pricing</span>
</a>
</td>
</tr></table>
</td></tr>

<!-- Sign-off -->
<tr><td style="padding:16px 32px 20px;">
<p style="margin:0 0 4px;color:#e2e8f0;font-size:14px;">Cheers,</p>
<p style="margin:0;color:#e2e8f0;font-size:14px;font-weight:600;">The HireIQ Team</p>
<p style="margin:2px 0 0;color:#6b7280;font-size:12px;"><a href="{_tracked_url(WEBSITE, email)}" style="color:#7c5cff;text-decoration:none;">hireiq.domato.ai</a></p>
</td></tr>

<!-- Footer -->
<tr><td style="padding:16px 32px;background-color:#0a0a14;border-top:1px solid #1e1e30;">
<p style="margin:0 0 6px;color:#64748b;font-size:11px;"><a href="{_tracked_url(WEBSITE, email)}" style="color:#7c5cff;text-decoration:none;font-weight:600;">HireIQ</a> &mdash; A Domato AI product &bull; ABN 94 695 794 346</p>
<p style="margin:6px 0 0;font-size:11px;">
<a href="{contact_url}" style="color:#7c5cff;text-decoration:none;">Contact Us</a>
<span style="color:#333;"> &bull; </span>
<a href="{unsub_url}" style="color:#64748b;text-decoration:none;">Unsubscribe</a>
<span style="color:#333;"> &bull; </span>
<a href="{_tracked_url(WEBSITE + '/privacy', email)}" style="color:#64748b;text-decoration:none;">Privacy</a>
<span style="color:#333;"> &bull; </span>
<a href="{_tracked_url(WEBSITE + '/terms', email)}" style="color:#64748b;text-decoration:none;">Terms</a>
</p>
</td></tr>

</table>
</td></tr>
</table>
<img src="{BACKEND_URL}/o?e={quote(email, safe='')}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;border:0;" />
</body>
</html>"""


# ── Login / Logout ───────────────────────────────────────────────

@router.post("/login")
async def login(request: Request):
    form = await request.form()
    user = form.get("username", "")
    pwd = form.get("password", "")
    if user == _USER and pwd == _PASS:
        resp = RedirectResponse("/api/admin/outreach", status_code=303)
        resp.set_cookie(_COOKIE, _make_token(), httponly=True, samesite="lax", max_age=_EXP_H * 3600)
        return resp
    return HTMLResponse(_login_html("Invalid credentials"), status_code=200)


@router.post("/logout")
async def logout():
    resp = RedirectResponse("/api/admin/outreach", status_code=303)
    resp.delete_cookie(_COOKIE)
    return resp


# ── Contact CRUD ─────────────────────────────────────────────────

class ContactBody(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    email: str
    phone: str | None = None
    website: str | None = None
    location: str | None = None
    industry: str | None = None
    role_type: str | None = None
    source: str | None = "manual"
    notes: str | None = None


class ContactUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    location: str | None = None
    industry: str | None = None
    role_type: str | None = None
    status: str | None = None
    notes: str | None = None


@router.get("/api/contacts")
async def list_contacts(
    status: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    search: str | None = None,
    limit: int = 200,
    offset: int = 0,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    query = select(OutreachContact)

    if status:
        query = query.where(OutreachContact.status == status)
    if industry:
        query = query.where(OutreachContact.industry.ilike(f"%{industry}%"))
    if country:
        query = query.where(OutreachContact.country == country.upper())
    if search:
        s = f"%{search}%"
        query = query.where(
            or_(
                OutreachContact.contact_name.ilike(s),
                OutreachContact.company_name.ilike(s),
                OutreachContact.email.ilike(s),
                OutreachContact.location.ilike(s),
            )
        )

    # Count total
    from sqlalchemy import text
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    query = query.order_by(OutreachContact.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return {
        "contacts": [c.to_dict() for c in contacts],
        "total": total,
    }


@router.post("/api/contacts")
async def create_contact(
    body: ContactBody,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    email_lower = body.email.lower()

    # Check for existing by email
    result = await db.execute(
        select(OutreachContact).where(OutreachContact.email == email_lower)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for k, v in body.model_dump(exclude_none=True).items():
            if k == "email":
                v = v.lower()
            setattr(existing, k, v)
        await db.flush()
        return {"contact": existing.to_dict(), "action": "updated"}

    contact = OutreachContact(
        email=email_lower,
        company_name=body.company_name,
        contact_name=body.contact_name,
        phone=body.phone,
        website=body.website,
        location=body.location,
        industry=body.industry,
        role_type=body.role_type,
        source=body.source or "manual",
        notes=body.notes,
    )
    db.add(contact)
    await db.flush()
    return {"contact": contact.to_dict(), "action": "created"}


@router.patch("/api/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    result = await db.execute(
        select(OutreachContact).where(OutreachContact.id == uuid.UUID(contact_id))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    for k, v in body.model_dump(exclude_none=True).items():
        if k == "email":
            v = v.lower()
        setattr(contact, k, v)
    await db.flush()
    return {"contact": contact.to_dict()}


@router.delete("/api/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    result = await db.execute(
        select(OutreachContact).where(OutreachContact.id == uuid.UUID(contact_id))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)
    await db.delete(contact)
    return {"ok": True}


# ── CSV Import ───────────────────────────────────────────────────

@router.post("/api/import")
async def import_csv(
    file: UploadFile = File(...),
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content))

    created = 0
    updated = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip().lower()
        company = (row.get("company_name") or "").strip()
        contact_name_val = (row.get("contact_name") or "").strip()

        if not email and not company and not contact_name_val:
            errors.append(f"Row {i}: need at least email, company_name, or contact_name")
            continue

        # Find existing by email
        existing = None
        if email and "@" in email:
            result = await db.execute(
                select(OutreachContact).where(OutreachContact.email == email)
            )
            existing = result.scalar_one_or_none()

        if existing:
            for field in ["company_name", "contact_name", "phone", "website", "location", "industry", "role_type", "notes"]:
                val = (row.get(field) or "").strip()
                if val:
                    setattr(existing, field, val)
            if email and "@" in email:
                existing.email = email
            existing.source = row.get("source", "").strip() or existing.source or "csv_import"
            updated += 1
        else:
            contact = OutreachContact(
                email=email if email and "@" in email else None,
                company_name=company or None,
                contact_name=contact_name_val or None,
                phone=(row.get("phone") or "").strip() or None,
                website=(row.get("website") or "").strip() or None,
                location=(row.get("location") or "").strip() or None,
                industry=(row.get("industry") or "").strip() or None,
                role_type=(row.get("role_type") or "").strip() or None,
                source=(row.get("source") or "").strip() or "csv_import",
                notes=(row.get("notes") or "").strip() or None,
            )
            db.add(contact)
            created += 1

    await db.flush()
    return {"created": created, "updated": updated, "errors": errors}


# ── Send email ───────────────────────────────────────────────────

@router.post("/api/send/{contact_id}")
async def send_email(
    contact_id: str,
    test: bool = Query(False),
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    result = await db.execute(
        select(OutreachContact).where(OutreachContact.id == uuid.UUID(contact_id))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    if contact.unsubscribed:
        return JSONResponse({"error": "Contact has unsubscribed"}, 400)

    contact_dict = contact.to_dict()
    email_config = await _load_email_config(db)
    from app.services.email_template import build_email_html, build_subject
    html = build_email_html(contact_dict, email_config, BACKEND_URL)
    html = html.replace("__UNSUB_TOKEN__", _hmac_token(contact.email or ""))
    subject = build_subject(contact_dict, email_config)
    to_email = FROM_EMAIL if test else (contact.email or "")

    smtp_result = _send_email_smtp(to_email, subject, html)

    log_entry = OutreachSendLog(
        contact_id=contact.id,
        email=to_email,
        send_type="test" if test else "manual",
        status=smtp_result["status"],
        subject=subject,
        notes=smtp_result.get("error") or None,
    )
    db.add(log_entry)

    if not test:
        contact.status = smtp_result["status"]
        contact.send_count = (contact.send_count or 0) + 1
        contact.date_contacted = datetime.now(timezone.utc)

    await db.flush()
    return {"ok": smtp_result["ok"], "status": smtp_result["status"], "error": smtp_result.get("error", "")}


@router.post("/api/send-batch")
async def send_batch(
    new_limit: int = Query(5),
    followup_limit: int = Query(5),
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    # New contacts (never sent)
    new_result = await db.execute(
        select(OutreachContact).where(
            and_(
                OutreachContact.status == "not_started",
                OutreachContact.unsubscribed == False,
                OutreachContact.email.isnot(None),
            )
        ).order_by(OutreachContact.created_at).limit(new_limit)
    )
    new_contacts = list(new_result.scalars().all())

    # Follow-up contacts (sent 7+ days ago)
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    followup_result = await db.execute(
        select(OutreachContact).where(
            and_(
                OutreachContact.status.in_(["sent", "delivered"]),
                OutreachContact.unsubscribed == False,
                OutreachContact.date_contacted.isnot(None),
                OutreachContact.date_contacted < cutoff,
            )
        ).order_by(OutreachContact.date_contacted).limit(followup_limit)
    )
    followup_contacts = list(followup_result.scalars().all())

    email_config = await _load_email_config(db)
    from app.services.email_template import build_email_html, build_subject

    results = []
    for contact in new_contacts + followup_contacts:
        contact_dict = contact.to_dict()
        html = build_email_html(contact_dict, email_config, BACKEND_URL)
        html = html.replace("__UNSUB_TOKEN__", _hmac_token(contact.email or ""))
        subject = build_subject(contact_dict, email_config)
        email = contact.email or ""
        smtp_result = _send_email_smtp(email, subject, html)

        log_entry = OutreachSendLog(
            contact_id=contact.id,
            email=email,
            send_type="batch",
            status=smtp_result["status"],
            subject=subject,
            notes=smtp_result.get("error") or None,
        )
        db.add(log_entry)
        contact.status = smtp_result["status"]
        contact.send_count = (contact.send_count or 0) + 1
        contact.date_contacted = datetime.now(timezone.utc)

        results.append({"email": email, "status": smtp_result["status"]})

    await db.flush()
    return {"sent": len(results), "results": results}


# ── Email Template Config ─────────────────────────────────────────

async def _load_email_config(db: AsyncSession) -> dict:
    """Load email template config from DB, merged with defaults."""
    from app.services.email_template import get_config_with_defaults
    from sqlalchemy import text
    row = await db.execute(text("SELECT config FROM outreach_email_config WHERE id = 'default'"))
    saved = row.scalar_one_or_none()
    return get_config_with_defaults(saved)


@router.get("/api/template")
async def get_template_config(
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Get the current email template config (merged with defaults)."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)
    config = await _load_email_config(db)
    return config


@router.put("/api/template")
async def save_template_config(
    request: Request,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Save email template config (partial update — only saves provided keys)."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)
    body = await request.json()
    from sqlalchemy import text
    await db.execute(
        text("""
            INSERT INTO outreach_email_config (id, config, updated_at)
            VALUES ('default', :config::jsonb, NOW())
            ON CONFLICT (id) DO UPDATE SET config = :config::jsonb, updated_at = NOW()
        """),
        {"config": __import__("json").dumps(body)},
    )
    await db.flush()
    return {"ok": True}


@router.get("/api/template/preview")
async def preview_template(
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Preview the email template with sample data."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)
    from app.services.email_template import build_email_html, build_subject
    config = await _load_email_config(db)
    sample_contact = {
        "contact_name": "Jane Smith",
        "company_name": "Acme Recruitment",
        "email": "preview@example.com",
        "industry": "tech",
    }
    html = build_email_html(sample_contact, config, BACKEND_URL)
    html = html.replace("__UNSUB_TOKEN__", "preview")
    subject = build_subject(sample_contact, config)
    return HTMLResponse(f"<h3 style='font-family:system-ui;padding:12px;background:#111;color:#ccc;margin:0;'>Subject: {subject}</h3>{html}")


# ── Stats ────────────────────────────────────────────────────────

@router.get("/api/stats")
async def get_stats(
    country: str | None = None,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    from app.models.user import User

    # Base filter for country
    country_filter = OutreachContact.country == country.upper() if country else True

    # Status counts
    status_result = await db.execute(
        select(OutreachContact.status, func.count())
        .where(country_filter)
        .group_by(OutreachContact.status)
    )
    status_counts = dict(status_result.all())
    total = sum(status_counts.values())

    # Engagement (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # Build per-email engagement lookup from clicks table
    opened_result = await db.execute(
        select(OutreachClick.email).where(OutreachClick.url == "__open__").distinct()
    )
    opened_emails = set(r[0] for r in opened_result.all() if r[0])

    clicked_result = await db.execute(
        select(OutreachClick.email).where(OutreachClick.url != "__open__").distinct()
    )
    clicked_emails = set(r[0] for r in clicked_result.all() if r[0])

    opens_count = await db.execute(
        select(func.count()).select_from(OutreachClick).where(
            and_(OutreachClick.url == "__open__", OutreachClick.created_at >= thirty_days_ago)
        )
    )
    opens = opens_count.scalar() or 0

    clicks_count = await db.execute(
        select(func.count()).select_from(OutreachClick).where(
            and_(OutreachClick.url != "__open__", OutreachClick.created_at >= thirty_days_ago)
        )
    )
    clicks = clicks_count.scalar() or 0

    # Cross-reference with HireIQ signups
    user_result = await db.execute(select(User.email))
    signed_up_emails = set(r[0].lower() for r in user_result.all() if r[0])

    # All contact emails for funnel
    contact_emails_result = await db.execute(
        select(OutreachContact.email).where(OutreachContact.email.isnot(None))
    )
    all_contact_emails = set(r[0].lower() for r in contact_emails_result.all() if r[0])

    sent_emails_result = await db.execute(
        select(OutreachContact.email).where(
            and_(
                OutreachContact.status.in_(["sent", "delivered"]),
                OutreachContact.email.isnot(None),
            )
        )
    )
    sent_emails = set(r[0].lower() for r in sent_emails_result.all() if r[0])

    funnel = {
        "total_contacts": total,
        "with_email": len(all_contact_emails),
        "sent": len(sent_emails),
        "opened": len(opened_emails & all_contact_emails),
        "clicked": len(clicked_emails & all_contact_emails),
        "signed_up": len(signed_up_emails & all_contact_emails),
        "used_analysis": 0,  # TODO: cross-ref with usage_events when needed
    }

    # Per-contact engagement
    contact_engagement: dict[str, dict] = {}
    for email in all_contact_emails:
        contact_engagement[email] = {
            "opened": email in opened_emails,
            "clicked": email in clicked_emails,
            "signed_up": email in signed_up_emails,
            "used_analysis": False,
        }

    # Recent sends
    recent_result = await db.execute(
        select(OutreachSendLog).order_by(OutreachSendLog.created_at.desc()).limit(20)
    )
    recent = recent_result.scalars().all()

    return {
        "total": total,
        "status_counts": status_counts,
        "engagement": {"opens": opens, "clicks": clicks},
        "funnel": funnel,
        "contact_engagement": contact_engagement,
        "recent_sends": [
            {
                "email": s.email,
                "send_type": s.send_type,
                "status": s.status,
                "subject": s.subject,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in recent
        ],
    }


# ── Click/Open tracking (public, no auth) ────────────────────────

@tracking_router.get("/r")
async def track_click(
    u: str = "",
    e: str = "",
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    url = unquote(u)
    email = unquote(e)
    if email:
        click = OutreachClick(
            email=email.lower(),
            url=url[:2000],
            ip=(request.client.host if request and request.client else None),
            user_agent=(request.headers.get("user-agent", "")[:500] if request else None),
        )
        db.add(click)
        await db.flush()
    return RedirectResponse(url or WEBSITE, status_code=302)


@tracking_router.get("/o")
async def track_open(
    e: str = "",
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    email = unquote(e)
    if email:
        click = OutreachClick(
            email=email.lower(),
            url="__open__",
            ip=(request.client.host if request and request.client else None),
            user_agent=(request.headers.get("user-agent", "")[:500] if request else None),
        )
        db.add(click)
        await db.flush()
    # 1x1 transparent GIF
    gif = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
    return Response(content=gif, media_type="image/gif", headers={"Cache-Control": "no-store"})


# ── Unsubscribe (public) ─────────────────────────────────────────

@router.get("/unsubscribe")
async def unsubscribe(
    e: str = "",
    t: str = "",
    db: AsyncSession = Depends(get_db),
):
    email = unquote(e).lower()
    if not email or _hmac_token(email) != t:
        return HTMLResponse("<h2>Invalid unsubscribe link.</h2>", status_code=400)

    result = await db.execute(
        select(OutreachContact).where(OutreachContact.email == email)
    )
    contact = result.scalar_one_or_none()
    if contact:
        contact.unsubscribed = True
        contact.status = "unsubscribed"
        await db.flush()

    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Unsubscribed</title></head>
<body style="font-family:system-ui;display:flex;justify-content:center;padding:60px 20px;background:#0a0a0a;">
<div style="max-width:440px;text-align:center;">
<h1 style="color:#e2e8f0;font-size:24px;">You&rsquo;ve been unsubscribed</h1>
<p style="color:#94a3b8;font-size:15px;">
You won&rsquo;t receive any more emails from HireIQ. If this was a mistake, contact
<a href="mailto:support@domato.ai" style="color:#7c5cff;">support@domato.ai</a>.
</p>
</div></body></html>""")


# ── Enrichment & Scraping ────────────────────────────────────────

@router.post("/api/enrich/{contact_id}")
async def enrich_contact(
    contact_id: str,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Scrape a contact's website for email addresses."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    result = await db.execute(
        select(OutreachContact).where(OutreachContact.id == uuid.UUID(contact_id))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    if not contact.website:
        return JSONResponse({"error": "No website URL on this contact"}, 400)

    scrape_result = await scrape_website_for_emails(contact.website)

    had_email = bool(contact.email)
    if scrape_result["emails"] and not had_email:
        contact.email = scrape_result["emails"][0]
        contact.source = contact.source or "enriched"
        await db.flush()

    return {
        "contact_id": contact_id,
        "website": contact.website,
        "emails_found": scrape_result["emails"],
        "pages_checked": scrape_result["pages_checked"],
        "auto_set": scrape_result["emails"][0] if scrape_result["emails"] and not had_email else None,
    }


@router.post("/api/enrich-batch")
async def enrich_batch(
    limit: int = Query(20),
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Scrape websites for contacts that have a website but no email."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    candidates_result = await db.execute(
        select(OutreachContact).where(
            and_(
                OutreachContact.website.isnot(None),
                or_(OutreachContact.email.is_(None), OutreachContact.email == ""),
                OutreachContact.unsubscribed == False,
                or_(
                    OutreachContact.enrich_status.is_(None),
                    ~OutreachContact.enrich_status.in_(["enriched_no_email", "enrich_error"]),
                ),
            )
        ).limit(limit)
    )
    candidates = list(candidates_result.scalars().all())

    results = []
    for contact in candidates:
        try:
            scrape_result = await scrape_website_for_emails(contact.website)
            if scrape_result["emails"]:
                contact.email = scrape_result["emails"][0]
                contact.enrich_status = "enriched"
                results.append({
                    "company": contact.company_name,
                    "website": contact.website,
                    "email": scrape_result["emails"][0],
                    "all_emails": scrape_result["emails"],
                })
            else:
                contact.enrich_status = "enriched_no_email"
                results.append({
                    "company": contact.company_name,
                    "website": contact.website,
                    "email": None,
                    "all_emails": [],
                })
        except Exception as exc:
            contact.enrich_status = "enrich_error"
            results.append({
                "company": contact.company_name,
                "website": contact.website,
                "email": None,
                "error": str(exc),
            })

    await db.flush()
    enriched = sum(1 for r in results if r.get("email"))
    return {"processed": len(results), "enriched": enriched, "results": results}


@router.post("/api/scrape-directory")
async def scrape_directory(
    source: str = Query("google"),
    query: str = Query("recruitment agency Australia"),
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Scrape a directory for new agency contacts."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    if source == "rcsa":
        agencies = await scrape_rcsa_directory()
    else:
        agencies = await google_search_agencies(query)

    created = 0
    skipped = 0
    for agency in agencies:
        website = agency.get("website", "")
        email = agency.get("email", "")

        # Deduplicate by website or email
        dedup_conditions = []
        if website:
            dedup_conditions.append(OutreachContact.website == website)
        if email:
            dedup_conditions.append(OutreachContact.email == email)

        if dedup_conditions:
            exists_result = await db.execute(
                select(func.count()).select_from(OutreachContact).where(or_(*dedup_conditions))
            )
            if (exists_result.scalar() or 0) > 0:
                skipped += 1
                continue

        contact = OutreachContact(
            company_name=agency.get("company_name"),
            email=email or None,
            website=website or None,
            location=agency.get("location", "Australia"),
            industry=agency.get("industry", "general"),
            role_type="agency_director",
            source=agency.get("source", source),
        )
        db.add(contact)
        created += 1

    await db.flush()
    return {"source": source, "found": len(agencies), "created": created, "skipped": skipped}


@router.post("/api/seed")
async def seed_from_csv(
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Load the built-in AU agencies CSV as starter contacts."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "au_agencies.csv")
    csv_path = os.path.normpath(csv_path)

    if not os.path.exists(csv_path):
        return JSONResponse({"error": f"Seed CSV not found at {csv_path}"}, 404)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    created = 0
    skipped = 0
    for row in rows:
        website = (row.get("website") or "").strip()
        company = (row.get("company_name") or "").strip()

        if not company and not website:
            continue

        # Deduplicate by website
        if website:
            exists_result = await db.execute(
                select(func.count()).select_from(OutreachContact).where(
                    OutreachContact.website == website
                )
            )
            if (exists_result.scalar() or 0) > 0:
                skipped += 1
                continue

        contact = OutreachContact(
            company_name=company or None,
            website=website or None,
            location=(row.get("location") or "").strip() or "Australia",
            industry=(row.get("industry") or "").strip() or "general",
            role_type=(row.get("role_type") or "").strip() or "agency_director",
            source="au_agencies_csv",
        )
        db.add(contact)
        created += 1

    await db.flush()
    return {"total_in_csv": len(rows), "created": created, "skipped": skipped}


@router.post("/api/scrape-recruiters")
async def scrape_recruiters_from_agencies(
    limit: int = 10,
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Scrape team pages of seeded agencies to find individual recruiter names + emails."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    from app.services.recruiter_scraper import scrape_agency_for_recruiters

    # Find agency contacts with websites that we haven't scraped yet
    agencies_result = await db.execute(
        select(OutreachContact).where(
            and_(
                OutreachContact.website.isnot(None),
                OutreachContact.source.in_(["au_agencies_csv", "google_search", "rcsa_directory"]),
                OutreachContact.recruiters_scraped == False,
            )
        ).limit(limit)
    )
    agencies_to_scrape = list(agencies_result.scalars().all())

    total_recruiters = 0
    agencies_processed = 0
    results = []

    for agency in agencies_to_scrape:
        website = agency.website
        company = agency.company_name or "Unknown"

        try:
            recruiters = await scrape_agency_for_recruiters(website)

            for person in recruiters:
                name = person.get("contact_name", "")
                email = person.get("email")

                if not name:
                    continue

                # Skip if we already have this person
                exists_result = await db.execute(
                    select(func.count()).select_from(OutreachContact).where(
                        and_(
                            OutreachContact.contact_name == name,
                            OutreachContact.company_name == company,
                        )
                    )
                )
                if (exists_result.scalar() or 0) > 0:
                    continue

                new_contact = OutreachContact(
                    company_name=company,
                    contact_name=name,
                    email=email,
                    website=website,
                    location=agency.location or "Australia",
                    industry=agency.industry or "general",
                    role_type="recruiter",
                    source=person.get("source", "team_page_scrape"),
                    notes=f"Guessed emails: {', '.join(person.get('guessed_emails', [])[:3])}" if person.get("guessed_emails") else None,
                )
                db.add(new_contact)
                total_recruiters += 1

            # Mark this agency as scraped
            agency.recruiters_scraped = True
            agencies_processed += 1

            results.append({
                "agency": company,
                "website": website,
                "recruiters_found": len(recruiters),
            })

        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", website, exc)
            agency.recruiters_scraped = True
            results.append({"agency": company, "website": website, "error": str(exc)})

    await db.flush()
    return {
        "agencies_processed": agencies_processed,
        "total_recruiters_found": total_recruiters,
        "results": results,
    }


# ── HTML Dashboard ───────────────────────────────────────────────

def _login_html(error: str = "") -> str:
    err_div = f'<div style="color:#ef4444;margin-bottom:16px;font-size:13px;">{error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HireIQ Outreach</title></head>
<body style="margin:0;background:#0a0a0a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,-apple-system,sans-serif;">
<div style="background:#111118;border-radius:16px;padding:40px;width:360px;box-shadow:0 8px 32px rgba(0,0,0,0.6);border:1px solid #1e1e30;">
<h1 style="color:#e2e8f0;margin:0 0 4px;font-size:22px;"><span style="color:#fff;">Hire</span><span style="color:#7c5cff;">IQ</span> Outreach</h1>
<p style="color:#64748b;margin:0 0 24px;font-size:13px;">Recruiter acquisition dashboard</p>
{err_div}
<form method="POST" action="/api/admin/outreach/login">
<input name="username" placeholder="Username" value="" style="width:100%;padding:10px 14px;margin-bottom:12px;border:1px solid #2a2a40;border-radius:8px;background:#0a0a14;color:#e2e8f0;font-size:14px;box-sizing:border-box;" />
<input name="password" type="password" placeholder="Password" style="width:100%;padding:10px 14px;margin-bottom:20px;border:1px solid #2a2a40;border-radius:8px;background:#0a0a14;color:#e2e8f0;font-size:14px;box-sizing:border-box;" />
<button type="submit" style="width:100%;padding:12px;border:none;border-radius:8px;background:#7c5cff;color:#fff;font-size:14px;font-weight:600;cursor:pointer;">Sign In</button>
</form>
</div></body></html>"""


@router.get("/")
async def dashboard(
    hiq_outreach: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify(hiq_outreach):
        return _unauth()

    # Fetch stats for KPI cards
    status_result = await db.execute(
        select(OutreachContact.status, func.count()).group_by(OutreachContact.status)
    )
    status_counts = dict(status_result.all())
    total = sum(status_counts.values())

    return HTMLResponse(_dashboard_html(total, status_counts))


def _dashboard_html(total: int, status_counts: dict) -> str:
    def kpi(label, value, color="#7c5cff"):
        return f'<div style="background:#111118;border-radius:12px;padding:16px 20px;min-width:120px;border:1px solid #1e1e30;"><p style="margin:0;color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">{label}</p><p style="margin:4px 0 0;color:{color};font-size:24px;font-weight:700;">{value}</p></div>'

    kpi_html = "".join([
        kpi("Total", total, "#e2e8f0"),
        kpi("Not Started", status_counts.get("not_started", 0), "#94a3b8"),
        kpi("Sent", status_counts.get("sent", 0), "#3b82f6"),
        kpi("Delivered", status_counts.get("delivered", 0), "#22c55e"),
        kpi("Bounced", status_counts.get("bounced", 0), "#f59e0b"),
        kpi("Failed", status_counts.get("failed", 0), "#ef4444"),
        kpi("Responded", status_counts.get("responded", 0), "#8b5cf6"),
        kpi("Unsub", status_counts.get("unsubscribed", 0), "#64748b"),
    ])

    industry_options = "".join(f'<option value="{s}">{s.title()}</option>' for s in INDUSTRIES)
    status_options = "".join(f'<option value="{s}">{s}</option>' for s in STATUSES)
    role_type_options = "".join(f'<option value="{s}">{s.replace("_"," ").title()}</option>' for s in ROLE_TYPES)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HireIQ Outreach</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a0a;color:#e2e8f0;font-family:system-ui,-apple-system,sans-serif;font-size:14px}}
.header{{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid #1e1e30}}
.header h1{{font-size:20px;font-weight:700}}
.tabs{{display:flex;gap:4px;padding:12px 24px;border-bottom:1px solid #1e1e30}}
.tab{{padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:500;color:#94a3b8;background:none;border:none}}
.tab:hover{{color:#e2e8f0;background:#111118}}
.tab.active{{color:#e2e8f0;background:#7c5cff}}
.content{{padding:24px}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}}
.toolbar{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;align-items:center}}
.toolbar select,.toolbar input{{padding:8px 12px;border:1px solid #2a2a40;border-radius:8px;background:#0a0a14;color:#e2e8f0;font-size:13px}}
.toolbar button,.btn{{padding:8px 16px;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600}}
.btn-primary{{background:#7c5cff;color:#fff}}.btn-primary:hover{{background:#6b4cee}}
.btn-danger{{background:#ef4444;color:#fff}}.btn-danger:hover{{background:#dc2626}}
.btn-success{{background:#22c55e;color:#fff}}.btn-success:hover{{background:#16a34a}}
.btn-sm{{padding:5px 10px;font-size:12px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 12px;color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;border-bottom:1px solid #1e1e30}}
td{{padding:10px 12px;border-bottom:1px solid #1e1e3020;font-size:13px}}
tr:hover{{background:#111118}}
.badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}}
.badge-sent{{background:#3b82f620;color:#60a5fa}}.badge-delivered{{background:#22c55e20;color:#4ade80}}
.badge-bounced{{background:#f59e0b20;color:#fbbf24}}.badge-failed{{background:#ef444420;color:#f87171}}
.badge-responded{{background:#8b5cf620;color:#a78bfa}}.badge-unsubscribed{{background:#64748b20;color:#94a3b8}}
.badge-not_started{{background:#2a2a40;color:#94a3b8}}
.enrich-none{{color:#ef4444;font-size:11px;font-style:italic}}.enrich-ok{{color:#4ade80;font-size:11px}}
.panel{{display:none}}.panel.active{{display:block}}
.card{{background:#111118;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #1e1e30}}
.form-row{{display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap}}
.form-row label{{display:block;color:#94a3b8;font-size:12px;margin-bottom:4px}}
.form-row input,.form-row select,.form-row textarea{{padding:8px 12px;border:1px solid #2a2a40;border-radius:8px;background:#0a0a14;color:#e2e8f0;font-size:13px;width:100%}}
.toast{{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;font-size:13px;font-weight:500;z-index:999;animation:fadeIn .3s}}
.toast-ok{{background:#22c55e;color:#fff}}.toast-err{{background:#ef4444;color:#fff}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(-10px)}}to{{opacity:1;transform:translateY(0)}}}}
.modal-bg{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:900;justify-content:center;align-items:center}}
.modal-bg.open{{display:flex}}
.modal{{background:#111118;border-radius:16px;padding:28px;width:500px;max-height:80vh;overflow-y:auto;border:1px solid #1e1e30}}
</style></head>
<body>

<div class="header">
<div style="display:flex;align-items:center;gap:12px;">
<h1><span style="color:#fff;">Hire</span><span style="color:#7c5cff;">IQ</span> Outreach</h1>
<span style="background:#7c5cff20;color:#a78bfa;padding:2px 10px;border-radius:6px;font-size:11px;">Recruiter Acquisition</span>
</div>
<form method="POST" action="/api/admin/outreach/logout" style="display:inline">
<button class="btn" style="background:#2a2a40;color:#94a3b8;">Sign Out</button>
</form>
</div>

<div class="tabs">
<button class="tab active" onclick="showTab('contacts')">Contacts</button>
<button class="tab" onclick="showTab('analytics')">Analytics</button>
<button class="tab" onclick="showTab('template')">Email Template</button>
</div>

<div class="content">

<!-- CONTACTS TAB -->
<div id="tab-contacts" class="panel active">
<div class="kpis">{kpi_html}</div>

<div class="toolbar">
<select id="f-country" onchange="loadContacts()" style="font-weight:600"><option value="">All Countries</option><option value="AU">AU</option><option value="US">US</option><option value="GB">UK</option><option value="CA">CA</option><option value="IN">IN</option><option value="SG">SG</option></select>
<select id="f-industry" onchange="loadContacts()"><option value="">All Industries</option>{industry_options}</select>
<select id="f-status" onchange="loadContacts()"><option value="">All Statuses</option>{status_options}</select>
<input id="f-search" placeholder="Search..." oninput="debounceSearch()" style="flex:1;min-width:180px;" />
<button class="btn btn-primary" onclick="openAddModal()">+ Add Contact</button>
<label class="btn btn-primary" style="cursor:pointer;">Import CSV<input type="file" accept=".csv" onchange="importCSV(this)" style="display:none"></label>
<button class="btn btn-success" onclick="sendBatch()">Send Batch</button>
</div>
<div class="toolbar" style="margin-top:-4px;">
<button class="btn" style="background:#1e3a5f;color:#60a5fa;" onclick="seedAgencies()">&#127968; Seed AU Agencies</button>
<button class="btn" style="background:#1a3a2a;color:#4ade80;" onclick="enrichEmails()">&#9993; Enrich Emails</button>
<button class="btn" style="background:#3a2a1a;color:#fb923c;" onclick="scrapeGoogle()">&#128269; Scrape Google</button>
<button class="btn" style="background:#2a1a3a;color:#c084fc;" onclick="scrapeRecruiters()">&#128100; Scrape Recruiters</button>
<span id="enrich-status" style="font-size:12px;color:#64748b;align-self:center;"></span>
</div>

<div id="contacts-table" style="overflow-x:auto;">
<table>
<thead><tr><th>Name</th><th>Company</th><th>Email</th><th style="text-align:center">Opened</th><th style="text-align:center">Clicked</th><th style="text-align:center">Signed Up</th><th style="text-align:center">Analysed</th><th>Status</th><th>Sends</th><th>Actions</th></tr></thead>
<tbody id="contacts-body"></tbody>
</table>
</div>
</div>

<!-- ANALYTICS TAB -->
<div id="tab-analytics" class="panel">
<div id="stats-content"><p style="color:#64748b;">Loading...</p></div>
</div>

<!-- TEMPLATE TAB -->
<div id="tab-template" class="panel">
<div style="display:flex;gap:20px;flex-wrap:wrap;">

<!-- Left: Editor -->
<div style="flex:1;min-width:340px;">
<div class="card">
<h3 style="margin-bottom:16px;color:#e2e8f0;">Email Template Editor</h3>
<p style="color:#64748b;font-size:12px;margin-bottom:16px;">Edit any field below. Changes apply to all future outreach emails.</p>

<div id="tpl-fields"></div>

<div style="display:flex;gap:12px;margin-top:16px;">
<button class="btn btn-primary" onclick="saveTemplate()">Save Template</button>
<button class="btn" style="background:#2a2a40;color:#e2e8f0;" onclick="resetTemplate()">Reset to Defaults</button>
</div>
</div>
</div>

<!-- Right: Preview -->
<div style="flex:1;min-width:340px;">
<div class="card" style="padding:0;overflow:hidden;">
<div style="padding:12px 16px;border-bottom:1px solid #1e1e30;display:flex;justify-content:space-between;align-items:center;">
<h3 style="color:#e2e8f0;font-size:14px;">Preview</h3>
<button class="btn btn-sm" style="background:#2a2a40;color:#94a3b8;" onclick="refreshPreview()">Refresh</button>
</div>
<iframe id="tpl-preview" style="width:100%;height:800px;border:none;background:#0a0a0a;" src=""></iframe>
</div>
</div>

</div>
</div>

</div>

<!-- ADD/EDIT MODAL -->
<div id="modal-bg" class="modal-bg" onclick="if(event.target===this)closeModal()">
<div class="modal">
<h3 id="modal-title" style="margin-bottom:16px;color:#e2e8f0;">Add Contact</h3>
<input type="hidden" id="m-id" />
<div class="form-row"><div style="flex:1"><label>Contact Name</label><input id="m-contact_name" /></div><div style="flex:1"><label>Company</label><input id="m-company_name" /></div></div>
<div class="form-row"><div style="flex:1"><label>Email*</label><input id="m-email" type="email" /></div><div style="flex:1"><label>Phone</label><input id="m-phone" /></div></div>
<div class="form-row"><div style="flex:1"><label>Website</label><input id="m-website" /></div><div style="flex:1"><label>Location</label><input id="m-location" /></div></div>
<div class="form-row"><div style="flex:1"><label>Industry</label><select id="m-industry"><option value="">--</option>{industry_options}</select></div><div style="flex:1"><label>Role Type</label><select id="m-role_type"><option value="">--</option>{role_type_options}</select></div></div>
<div class="form-row"><div style="flex:1"><label>Status</label><select id="m-status"><option value="">--</option>{status_options}</select></div><div style="flex:1"><label>Source</label><input id="m-source" value="manual" /></div></div>
<div class="form-row"><div style="flex:1"><label>Notes</label><textarea id="m-notes" rows="2"></textarea></div></div>
<div style="display:flex;gap:12px;justify-content:flex-end;margin-top:16px;">
<button class="btn" style="background:#2a2a40;color:#e2e8f0;" onclick="closeModal()">Cancel</button>
<button class="btn btn-primary" onclick="saveContact()">Save</button>
</div>
</div>
</div>

<script>
const API='/api/admin/outreach/api';
let searchTimer=null;

function showTab(t){{
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+t).classList.add('active');
  event.target.classList.add('active');
  if(t==='contacts')loadContacts();
  if(t==='analytics')loadStats();
  if(t==='template')loadTemplate();
}}

function toast(msg,ok=true){{
  const d=document.createElement('div');
  d.className='toast '+(ok?'toast-ok':'toast-err');
  d.textContent=msg;
  document.body.appendChild(d);
  setTimeout(()=>d.remove(),3000);
}}

async function api(path,opts={{}}){{
  const r=await fetch(API+path,opts);
  return r.json();
}}

let _contactEngagement={{}};

async function loadContacts(){{
  const country=document.getElementById('f-country').value;
  const industry=document.getElementById('f-industry').value;
  const status=document.getElementById('f-status').value;
  const search=document.getElementById('f-search').value;
  let qs='?limit=200';
  if(country)qs+='&country='+country;
  if(industry)qs+='&industry='+industry;
  if(status)qs+='&status='+status;
  if(search)qs+='&search='+encodeURIComponent(search);
  const data=await api('/contacts'+qs);
  // Fetch engagement data
  const stats=await api('/stats'+(country?'?country='+country:''));
  _contactEngagement=stats.contact_engagement||{{}};
  const tbody=document.getElementById('contacts-body');
  tbody.innerHTML=data.contacts.map(c=>{{
    const email=(c.email||'').toLowerCase();
    const eng=_contactEngagement[email]||{{}};
    const dot=(on,color)=>on?`<span style="color:${{color}};font-size:14px;" title="${{on?'Yes':'No'}}">&#9679;</span>`:`<span style="color:#333;font-size:14px;">&#9675;</span>`;
    return `<tr>
    <td>${{c.contact_name||'\u2014'}}</td>
    <td>${{c.company_name||'\u2014'}}</td>
    <td style="font-size:12px">${{c.email?`<span style="color:#4ade80">${{c.email}}</span>`:'<span style="color:#64748b;font-style:italic">no email</span>'}}</td>
    <td style="text-align:center">${{dot(eng.opened,'#22c55e')}}</td>
    <td style="text-align:center">${{dot(eng.clicked,'#3b82f6')}}</td>
    <td style="text-align:center">${{dot(eng.signed_up,'#a78bfa')}}</td>
    <td style="text-align:center">${{dot(eng.used_analysis,'#f59e0b')}}</td>
    <td><span class="badge badge-${{c.status}}">${{c.status}}</span></td>
    <td>${{c.send_count}}</td>
    <td style="white-space:nowrap">
      ${{c.email?`<button class="btn btn-sm btn-primary" onclick="sendTo('${{c.id}}',false)">Send</button>`:`<button class="btn btn-sm" style="background:#1a3a2a;color:#4ade80" onclick="enrichOne('${{c.id}}')">Enrich</button>`}}
      <button class="btn btn-sm" style="background:#2a2a40;color:#94a3b8" onclick="editContact('${{c.id}}')">Edit</button>
      <button class="btn btn-sm btn-danger" onclick="deleteContact('${{c.id}}')">Del</button>
    </td>
  </tr>`;
  }}).join('');
}}

function debounceSearch(){{clearTimeout(searchTimer);searchTimer=setTimeout(loadContacts,300)}}

async function sendTo(id,test){{
  if(!test&&!confirm('Send real email to this contact?'))return;
  const r=await api('/send/'+id+'?test='+test,{{method:'POST'}});
  toast(r.ok?(test?'Test sent!':'Sent: '+r.status):'Error: '+r.error,r.ok);
  if(!test)loadContacts();
}}

async function sendBatch(){{
  if(!confirm('Send batch emails (5 new + 5 follow-up)?'))return;
  const r=await api('/send-batch?new_limit=5&followup_limit=5',{{method:'POST'}});
  toast('Batch sent: '+r.sent+' emails',true);
  loadContacts();
}}

async function deleteContact(id){{
  if(!confirm('Delete this contact?'))return;
  await api('/contacts/'+id,{{method:'DELETE'}});
  toast('Deleted');
  loadContacts();
}}

function openAddModal(){{
  document.getElementById('modal-title').textContent='Add Contact';
  document.getElementById('m-id').value='';
  ['contact_name','company_name','email','phone','website','location','notes'].forEach(f=>document.getElementById('m-'+f).value='');
  document.getElementById('m-industry').value='';
  document.getElementById('m-role_type').value='';
  document.getElementById('m-status').value='';
  document.getElementById('m-source').value='manual';
  document.getElementById('modal-bg').classList.add('open');
}}

async function editContact(id){{
  const data=await api('/contacts?search='+id);
  const c=data.contacts.find(x=>x.id===id);
  if(!c)return;
  document.getElementById('modal-title').textContent='Edit Contact';
  document.getElementById('m-id').value=c.id;
  ['contact_name','company_name','email','phone','website','location','notes'].forEach(f=>document.getElementById('m-'+f).value=c[f]||'');
  document.getElementById('m-industry').value=c.industry||'';
  document.getElementById('m-role_type').value=c.role_type||'';
  document.getElementById('m-status').value=c.status||'';
  document.getElementById('m-source').value=c.source||'';
  document.getElementById('modal-bg').classList.add('open');
}}

function closeModal(){{document.getElementById('modal-bg').classList.remove('open')}}

async function saveContact(){{
  const id=document.getElementById('m-id').value;
  const body={{}};
  ['contact_name','company_name','email','phone','website','location','notes','source'].forEach(f=>{{
    const v=document.getElementById('m-'+f).value;if(v)body[f]=v;
  }});
  body.industry=document.getElementById('m-industry').value||null;
  body.role_type=document.getElementById('m-role_type').value||null;
  const st=document.getElementById('m-status').value;
  if(st)body.status=st;

  if(id){{
    await api('/contacts/'+id,{{method:'PATCH',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});
    toast('Contact updated');
  }}else{{
    if(!body.email){{toast('Email is required',false);return}}
    await api('/contacts',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});
    toast('Contact created');
  }}
  closeModal();
  loadContacts();
}}

async function importCSV(input){{
  const file=input.files[0];if(!file)return;
  const fd=new FormData();fd.append('file',file);
  const r=await fetch(API+'/import',{{method:'POST',body:fd}});
  const d=await r.json();
  toast('Imported: '+d.created+' new, '+d.updated+' updated'+(d.errors.length?' ('+d.errors.length+' errors)':''));
  input.value='';
  loadContacts();
}}

async function loadStats(){{
  const country=document.getElementById('f-country').value;
  const s=await api('/stats'+(country?'?country='+country:''));
  const eng=s.engagement||{{}};
  const f=s.funnel||{{}};
  let html='';

  // Funnel
  html+='<div class="card" style="margin-bottom:20px;"><h3 style="margin-bottom:16px;color:#e2e8f0;">Conversion Funnel</h3>';
  const steps=[
    {{label:'Total Contacts',value:f.total_contacts||0,color:'#64748b'}},
    {{label:'Have Email',value:f.with_email||0,color:'#94a3b8'}},
    {{label:'Email Sent',value:f.sent||0,color:'#60a5fa'}},
    {{label:'Opened',value:f.opened||0,color:'#22c55e'}},
    {{label:'Clicked',value:f.clicked||0,color:'#3b82f6'}},
    {{label:'Signed Up',value:f.signed_up||0,color:'#a78bfa'}},
    {{label:'Used Analysis',value:f.used_analysis||0,color:'#f59e0b'}},
  ];
  const maxVal=Math.max(1,...steps.map(s=>s.value));
  steps.forEach(st=>{{
    const pct=Math.round((st.value/maxVal)*100);
    html+=`<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
      <span style="width:110px;font-size:12px;color:#94a3b8;text-align:right">${{st.label}}</span>
      <div style="flex:1;height:28px;background:#111118;border-radius:6px;overflow:hidden;position:relative;">
        <div style="height:100%;width:${{pct}}%;background:${{st.color}};border-radius:6px;transition:width 0.5s;"></div>
        <span style="position:absolute;right:8px;top:5px;font-size:12px;font-weight:600;color:#e2e8f0;">${{st.value}}</span>
      </div>
    </div>`;
  }});
  html+='</div>';

  // KPI cards
  html+='<div class="kpis" style="margin-bottom:24px;">';
  html+='<div style="background:#111118;border-radius:12px;padding:16px 20px;border:1px solid #1e1e30;"><p style="color:#64748b;font-size:11px;text-transform:uppercase;">Opens (30d)</p><p style="color:#22c55e;font-size:24px;font-weight:700;">'+eng.opens+'</p></div>';
  html+='<div style="background:#111118;border-radius:12px;padding:16px 20px;border:1px solid #1e1e30;"><p style="color:#64748b;font-size:11px;text-transform:uppercase;">Clicks (30d)</p><p style="color:#3b82f6;font-size:24px;font-weight:700;">'+eng.clicks+'</p></div>';
  const signupRate=f.sent>0?Math.round((f.signed_up/f.sent)*100):0;
  html+='<div style="background:#111118;border-radius:12px;padding:16px 20px;border:1px solid #1e1e30;"><p style="color:#64748b;font-size:11px;text-transform:uppercase;">Signup Rate</p><p style="color:#a78bfa;font-size:24px;font-weight:700;">'+signupRate+'%</p></div>';
  html+='</div>';

  // Recent sends
  html+='<div class="card"><h3 style="margin-bottom:12px;">Recent Sends</h3><table><thead><tr><th>Email</th><th>Type</th><th>Status</th><th>Subject</th><th>Time</th></tr></thead><tbody>';
  (s.recent_sends||[]).forEach(r=>{{
    html+=`<tr><td style="font-size:12px">${{r.email}}</td><td>${{r.send_type}}</td><td><span class="badge badge-${{r.status}}">${{r.status}}</span></td><td style="font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{r.subject||''}}</td><td style="font-size:11px;color:#64748b">${{r.created_at?new Date(r.created_at).toLocaleString():''}}</td></tr>`;
  }});
  html+='</tbody></table></div>';
  document.getElementById('stats-content').innerHTML=html;
}}

async function seedAgencies(){{
  if(!confirm('Load built-in AU agencies CSV? This adds ~150 Australian recruitment agencies as contacts.'))return;
  const status=document.getElementById('enrich-status');
  status.textContent='Seeding...';
  const r=await api('/seed',{{method:'POST'}});
  if(r.error){{toast('Error: '+r.error,false);status.textContent='';return;}}
  toast('Seeded: '+r.created+' new agencies ('+r.skipped+' already existed)',true);
  status.textContent='Seeded '+r.created+' agencies';
  loadContacts();
}}

async function enrichEmails(){{
  if(!confirm('Scrape websites for contacts missing emails? (up to 20 contacts, may take a while)'))return;
  const status=document.getElementById('enrich-status');
  status.textContent='Enriching...';
  const r=await api('/enrich-batch?limit=20',{{method:'POST'}});
  if(r.error){{toast('Error: '+r.error,false);status.textContent='';return;}}
  toast('Enriched: '+r.enriched+' emails found out of '+r.processed+' contacts',true);
  status.textContent='Found '+r.enriched+'/'+r.processed+' emails';
  loadContacts();
}}

async function scrapeGoogle(){{
  const q=prompt('Search query:','recruitment agency Australia');
  if(!q)return;
  const status=document.getElementById('enrich-status');
  status.textContent='Scraping...';
  const r=await api('/scrape-directory?source=google&query='+encodeURIComponent(q),{{method:'POST'}});
  if(r.error){{toast('Error: '+r.error,false);status.textContent='';return;}}
  toast('Scraped: '+r.created+' new agencies found ('+r.skipped+' duplicates)',true);
  status.textContent='Imported '+r.created+' new agencies';
  loadContacts();
}}

async function scrapeRecruiters(){{
  if(!confirm('Scrape team pages of seeded agencies for individual recruiter names and emails? (processes 10 agencies, may take a minute)'))return;
  const status=document.getElementById('enrich-status');
  status.textContent='Scraping team pages...';
  const r=await api('/scrape-recruiters?limit=10',{{method:'POST'}});
  if(r.error){{toast('Error: '+r.error,false);status.textContent='';return;}}
  toast('Found '+r.total_recruiters_found+' recruiters from '+r.agencies_processed+' agencies',true);
  status.textContent=r.total_recruiters_found+' recruiters from '+r.agencies_processed+' agencies';
  loadContacts();
}}

async function enrichOne(id){{
  const status=document.getElementById('enrich-status');
  status.textContent='Enriching 1 contact...';
  const r=await api('/enrich/'+id,{{method:'POST'}});
  if(r.error){{toast('Error: '+r.error,false);status.textContent='';return;}}
  if(r.emails_found&&r.emails_found.length){{
    toast('Found: '+r.emails_found[0]+(r.auto_set?' (auto-set)':''),true);
  }}else{{
    toast('No emails found on '+r.website,false);
  }}
  status.textContent='';
  loadContacts();
}}

// ── Template Editor ──
let _tplConfig={{}};
const TPL_FIELDS=[
  {{section:'Brand',fields:[
    {{key:'brand_name',label:'Brand Name',type:'text'}},
    {{key:'brand_tagline',label:'Tagline',type:'text'}},
    {{key:'brand_tagline_bold',label:'Tagline (Bold)',type:'text'}},
    {{key:'website_url',label:'Website URL',type:'text'}},
    {{key:'company_legal',label:'Legal Line',type:'text'}},
  ]}},
  {{section:'Greeting',fields:[
    {{key:'greeting_template',label:'Greeting (use {{first_name}})',type:'text'}},
    {{key:'intro_template',label:'Intro (use {{company}})',type:'textarea'}},
  ]}},
  {{section:'Solution',fields:[
    {{key:'solution_text',label:'Solution Text (HTML ok)',type:'textarea'}},
  ]}},
  {{section:'CTA',fields:[
    {{key:'cta_headline',label:'CTA Headline',type:'text'}},
    {{key:'cta_subtext',label:'CTA Subtext',type:'text'}},
    {{key:'cta_button_text',label:'Button Text',type:'text'}},
    {{key:'cta_fine_print',label:'Fine Print',type:'text'}},
  ]}},
  {{section:'Subject Line',fields:[
    {{key:'subject_template',label:'Subject (use {{contact_name}})',type:'text'}},
  ]}},
  {{section:'Sign-off',fields:[
    {{key:'signoff_line1',label:'Line 1',type:'text'}},
    {{key:'signoff_line2',label:'Line 2',type:'text'}},
  ]}},
];

async function loadTemplate(){{
  _tplConfig=await api('/template');
  renderTemplateFields();
  refreshPreview();
}}

function renderTemplateFields(){{
  const container=document.getElementById('tpl-fields');
  let html='';
  TPL_FIELDS.forEach(section=>{{
    html+=`<div style="margin-bottom:16px;"><h4 style="color:#a78bfa;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">${{section.section}}</h4>`;
    section.fields.forEach(f=>{{
      const val=_tplConfig[f.key]||'';
      if(f.type==='textarea'){{
        html+=`<div class="form-row"><div style="flex:1"><label>${{f.label}}</label><textarea id="tpl-${{f.key}}" rows="3" style="font-size:12px;">${{val}}</textarea></div></div>`;
      }}else{{
        html+=`<div class="form-row"><div style="flex:1"><label>${{f.label}}</label><input id="tpl-${{f.key}}" value="${{String(val).replace(/"/g,'&quot;')}}" /></div></div>`;
      }}
    }});
    html+=`</div>`;
  }});

  // Pain points editor
  html+=`<div style="margin-bottom:16px;"><h4 style="color:#a78bfa;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Pain Points (by Industry)</h4>`;
  const pains=_tplConfig.pain_points||{{}};
  ['tech','healthcare','finance','agency','general'].forEach(ind=>{{
    const p=pains[ind]||{{}};
    html+=`<details style="margin-bottom:8px;"><summary style="color:#e2e8f0;font-size:12px;cursor:pointer;font-weight:600;">${{ind.charAt(0).toUpperCase()+ind.slice(1)}}</summary>
    <div class="form-row" style="margin-top:8px;"><div style="flex:1"><label>Headline</label><input id="tpl-pain-${{ind}}-headline" value="${{(p.headline||'').replace(/"/g,'&quot;')}}" /></div></div>
    <div class="form-row"><div style="flex:1"><label>Detail</label><textarea id="tpl-pain-${{ind}}-detail" rows="2" style="font-size:12px;">${{p.detail||''}}</textarea></div></div>
    </details>`;
  }});
  html+=`</div>`;

  // Features editor
  html+=`<div style="margin-bottom:16px;"><h4 style="color:#a78bfa;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Feature Cards</h4>`;
  const features=_tplConfig.features||[];
  features.forEach((f,i)=>{{
    html+=`<details style="margin-bottom:6px;"><summary style="color:#e2e8f0;font-size:12px;cursor:pointer;">${{f.icon}} ${{f.title}}</summary>
    <div class="form-row" style="margin-top:6px;">
    <div style="width:60px"><label>Icon</label><input id="tpl-feat-${{i}}-icon" value="${{f.icon}}" style="font-size:16px;text-align:center;" /></div>
    <div style="flex:1"><label>Title</label><input id="tpl-feat-${{i}}-title" value="${{f.title}}" /></div>
    </div>
    <div class="form-row"><div style="flex:1"><label>Description</label><input id="tpl-feat-${{i}}-desc" value="${{f.desc.replace(/"/g,'&quot;')}}" /></div></div>
    </details>`;
  }});
  html+=`</div>`;

  // KPIs editor
  html+=`<div style="margin-bottom:16px;"><h4 style="color:#a78bfa;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">KPI Row</h4>`;
  const kpis=_tplConfig.kpis||[];
  kpis.forEach((k,i)=>{{
    html+=`<div class="form-row">
    <div style="width:60px"><label>Icon</label><input id="tpl-kpi-${{i}}-icon" value="${{k.icon}}" style="font-size:16px;text-align:center;" /></div>
    <div style="width:80px"><label>Value</label><input id="tpl-kpi-${{i}}-value" value="${{k.value}}" /></div>
    <div style="flex:1"><label>Label</label><input id="tpl-kpi-${{i}}-label" value="${{k.label}}" /></div>
    </div>`;
  }});
  html+=`</div>`;

  container.innerHTML=html;
}}

function gatherTemplateData(){{
  const data={{}};
  TPL_FIELDS.forEach(s=>s.fields.forEach(f=>{{
    const el=document.getElementById('tpl-'+f.key);
    if(el)data[f.key]=el.value;
  }}));

  // Pain points
  data.pain_points={{}};
  ['tech','healthcare','finance','agency','general'].forEach(ind=>{{
    const h=document.getElementById('tpl-pain-'+ind+'-headline');
    const d=document.getElementById('tpl-pain-'+ind+'-detail');
    if(h&&d)data.pain_points[ind]={{headline:h.value,detail:d.value}};
  }});

  // Features
  data.features=[];
  for(let i=0;i<6;i++){{
    const icon=document.getElementById('tpl-feat-'+i+'-icon');
    const title=document.getElementById('tpl-feat-'+i+'-title');
    const desc=document.getElementById('tpl-feat-'+i+'-desc');
    if(icon&&title&&desc)data.features.push({{icon:icon.value,title:title.value,desc:desc.value}});
  }}

  // KPIs
  data.kpis=[];
  for(let i=0;i<3;i++){{
    const icon=document.getElementById('tpl-kpi-'+i+'-icon');
    const val=document.getElementById('tpl-kpi-'+i+'-value');
    const label=document.getElementById('tpl-kpi-'+i+'-label');
    if(icon&&val&&label)data.kpis.push({{icon:icon.value,value:val.value,label:label.value}});
  }}

  return data;
}}

async function saveTemplate(){{
  const data=gatherTemplateData();
  await api('/template',{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  toast('Template saved!');
  refreshPreview();
}}

async function resetTemplate(){{
  if(!confirm('Reset all template fields to defaults?'))return;
  await api('/template',{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{}})}});
  toast('Template reset to defaults');
  await loadTemplate();
}}

function refreshPreview(){{
  document.getElementById('tpl-preview').src=API+'/template/preview?t='+Date.now();
}}

// Initial load
loadContacts();
</script>
</body></html>"""
