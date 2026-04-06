"""
Outreach management — recruiter/HR contact CRUD, email campaigns, tracking.

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
from fastapi import APIRouter, Cookie, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel

from app.config import get_settings
from app.services.recruiter_scraper import scrape_website_for_emails, scrape_rcsa_directory, google_search_agencies

logger = logging.getLogger(__name__)

settings = get_settings()

router = APIRouter(prefix="/api/admin/outreach", tags=["outreach"])
tracking_router = APIRouter(tags=["outreach-tracking"])

# ── In-memory storage ────────────────────────────────────────────
_contacts: dict[str, dict] = {}        # id -> contact dict
_send_log: list[dict] = []             # send history
_clicks: list[dict] = []               # click/open tracking
_config: dict[str, str] = {}           # key-value config

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
    features_url = _tracked_url(WEBSITE, email)  # Single-page app — features are on the homepage
    pricing_url = _tracked_url(WEBSITE, email)   # Pricing is inline on the homepage
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


def _contact_dict(c: dict) -> dict:
    return {
        "id": c.get("id", ""),
        "company_name": c.get("company_name"),
        "contact_name": c.get("contact_name"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "website": c.get("website"),
        "location": c.get("location"),
        "industry": c.get("industry"),
        "role_type": c.get("role_type"),
        "source": c.get("source"),
        "status": c.get("status", "not_started"),
        "unsubscribed": c.get("unsubscribed", False),
        "send_count": c.get("send_count", 0),
        "date_contacted": c.get("date_contacted"),
        "notes": c.get("notes"),
        "created_at": c.get("created_at"),
    }


@router.get("/api/contacts")
async def list_contacts(
    status: str | None = None,
    industry: str | None = None,
    search: str | None = None,
    limit: int = 200,
    offset: int = 0,
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    contacts = list(_contacts.values())

    # Filters
    if status:
        contacts = [c for c in contacts if c.get("status") == status]
    if industry:
        contacts = [c for c in contacts if industry.lower() in (c.get("industry") or "").lower()]
    if search:
        s = search.lower()
        contacts = [c for c in contacts if (
            s in (c.get("contact_name") or "").lower()
            or s in (c.get("company_name") or "").lower()
            or s in (c.get("email") or "").lower()
            or s in (c.get("location") or "").lower()
        )]

    # Sort by created_at desc
    contacts.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    total = len(contacts)
    contacts = contacts[offset:offset + limit]

    return {
        "contacts": [_contact_dict(c) for c in contacts],
        "total": total,
    }


@router.post("/api/contacts")
async def create_contact(
    body: ContactBody,
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    email_lower = body.email.lower()

    # Check for existing by email
    existing = None
    for c in _contacts.values():
        if c.get("email") == email_lower:
            existing = c
            break

    if existing:
        for k, v in body.model_dump(exclude_none=True).items():
            if k == "email":
                v = v.lower()
            existing[k] = v
        return {"contact": _contact_dict(existing), "action": "updated"}

    cid = str(uuid.uuid4())
    contact = {
        "id": cid,
        "email": email_lower,
        "company_name": body.company_name,
        "contact_name": body.contact_name,
        "phone": body.phone,
        "website": body.website,
        "location": body.location,
        "industry": body.industry,
        "role_type": body.role_type,
        "source": body.source or "manual",
        "status": "not_started",
        "unsubscribed": False,
        "send_count": 0,
        "date_contacted": None,
        "notes": body.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _contacts[cid] = contact
    return {"contact": _contact_dict(contact), "action": "created"}


@router.patch("/api/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    contact = _contacts.get(contact_id)
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    for k, v in body.model_dump(exclude_none=True).items():
        if k == "email":
            v = v.lower()
        contact[k] = v
    return {"contact": _contact_dict(contact)}


@router.delete("/api/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    if contact_id not in _contacts:
        return JSONResponse({"error": "Not found"}, 404)
    del _contacts[contact_id]
    return {"ok": True}


# ── CSV Import ───────────────────────────────────────────────────

@router.post("/api/import")
async def import_csv(
    file: UploadFile = File(...),
    hiq_outreach: str | None = Cookie(None),
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
            for c in _contacts.values():
                if c.get("email") == email:
                    existing = c
                    break

        if existing:
            for field in ["company_name", "contact_name", "phone", "website", "location", "industry", "role_type", "notes"]:
                val = (row.get(field) or "").strip()
                if val:
                    existing[field] = val
            if email and "@" in email:
                existing["email"] = email
            existing["source"] = row.get("source", "").strip() or existing.get("source") or "csv_import"
            updated += 1
        else:
            cid = str(uuid.uuid4())
            contact = {
                "id": cid,
                "email": email if email and "@" in email else None,
                "company_name": company or None,
                "contact_name": contact_name_val or None,
                "phone": (row.get("phone") or "").strip() or None,
                "website": (row.get("website") or "").strip() or None,
                "location": (row.get("location") or "").strip() or None,
                "industry": (row.get("industry") or "").strip() or None,
                "role_type": (row.get("role_type") or "").strip() or None,
                "source": (row.get("source") or "").strip() or "csv_import",
                "status": "not_started",
                "unsubscribed": False,
                "send_count": 0,
                "date_contacted": None,
                "notes": (row.get("notes") or "").strip() or None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            _contacts[cid] = contact
            created += 1

    return {"created": created, "updated": updated, "errors": errors}


# ── Send email ───────────────────────────────────────────────────

@router.post("/api/send/{contact_id}")
async def send_email(
    contact_id: str,
    test: bool = Query(False),
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    contact = _contacts.get(contact_id)
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    if contact.get("unsubscribed"):
        return JSONResponse({"error": "Contact has unsubscribed"}, 400)

    html = _build_email_html(contact)
    cname = contact.get("contact_name") or "you"
    subject = f"Stop spending hours screening resumes — {cname}"
    to_email = FROM_EMAIL if test else contact.get("email", "")

    result = _send_email_smtp(to_email, subject, html)

    _send_log.append({
        "id": str(uuid.uuid4()),
        "contact_id": contact_id,
        "email": to_email,
        "send_type": "test" if test else "manual",
        "status": result["status"],
        "subject": subject,
        "notes": result.get("error") or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    if not test:
        contact["status"] = result["status"]
        contact["send_count"] = (contact.get("send_count") or 0) + 1
        contact["date_contacted"] = datetime.now(timezone.utc).isoformat()

    return {"ok": result["ok"], "status": result["status"], "error": result.get("error", "")}


@router.post("/api/send-batch")
async def send_batch(
    new_limit: int = Query(5),
    followup_limit: int = Query(5),
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    # New contacts (never sent)
    all_contacts = list(_contacts.values())
    new_contacts = [
        c for c in all_contacts
        if c.get("status") == "not_started" and not c.get("unsubscribed")
    ]
    new_contacts.sort(key=lambda c: c.get("created_at", ""))
    new_contacts = new_contacts[:new_limit]

    # Follow-up contacts (sent 7+ days ago)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    followup_contacts = [
        c for c in all_contacts
        if c.get("status") in ("sent", "delivered")
        and not c.get("unsubscribed")
        and c.get("date_contacted")
        and c["date_contacted"] < cutoff
    ]
    followup_contacts.sort(key=lambda c: c.get("date_contacted", ""))
    followup_contacts = followup_contacts[:followup_limit]

    results = []
    for contact in new_contacts + followup_contacts:
        html = _build_email_html(contact)
        cname = contact.get("contact_name") or "you"
        subject = f"Stop spending hours screening resumes — {cname}"
        email = contact.get("email", "")
        result = _send_email_smtp(email, subject, html)

        _send_log.append({
            "id": str(uuid.uuid4()),
            "contact_id": contact["id"],
            "email": email,
            "send_type": "batch",
            "status": result["status"],
            "subject": subject,
            "notes": result.get("error") or None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        contact["status"] = result["status"]
        contact["send_count"] = (contact.get("send_count") or 0) + 1
        contact["date_contacted"] = datetime.now(timezone.utc).isoformat()

        results.append({"email": email, "status": result["status"]})

    return {"sent": len(results), "results": results}


# ── Stats ────────────────────────────────────────────────────────

@router.get("/api/stats")
async def get_stats(
    hiq_outreach: str | None = Cookie(None),
):
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    # Status counts
    status_counts: dict[str, int] = {}
    for c in _contacts.values():
        s = c.get("status", "not_started")
        status_counts[s] = status_counts.get(s, 0) + 1
    total = sum(status_counts.values())

    # Engagement (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    opens = sum(
        1 for cl in _clicks
        if cl.get("url") == "__open__" and cl.get("created_at", "") >= thirty_days_ago
    )
    clicks = sum(
        1 for cl in _clicks
        if cl.get("url") != "__open__" and cl.get("created_at", "") >= thirty_days_ago
    )

    # Recent sends
    recent = sorted(_send_log, key=lambda s: s.get("created_at", ""), reverse=True)[:20]

    return {
        "total": total,
        "status_counts": status_counts,
        "engagement": {"opens": opens, "clicks": clicks},
        "recent_sends": [
            {
                "email": s.get("email"),
                "send_type": s.get("send_type"),
                "status": s.get("status"),
                "subject": s.get("subject"),
                "created_at": s.get("created_at"),
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
):
    url = unquote(u)
    email = unquote(e)
    if email:
        _clicks.append({
            "id": str(uuid.uuid4()),
            "email": email.lower(),
            "url": url[:1000],
            "ip": (request.client.host if request and request.client else None),
            "user_agent": (request.headers.get("user-agent", "")[:500] if request else None),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return RedirectResponse(url or WEBSITE, status_code=302)


@tracking_router.get("/o")
async def track_open(
    e: str = "",
    request: Request = None,
):
    email = unquote(e)
    if email:
        _clicks.append({
            "id": str(uuid.uuid4()),
            "email": email.lower(),
            "url": "__open__",
            "ip": (request.client.host if request and request.client else None),
            "user_agent": (request.headers.get("user-agent", "")[:500] if request else None),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    # 1x1 transparent GIF
    gif = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
    return Response(content=gif, media_type="image/gif", headers={"Cache-Control": "no-store"})


# ── Unsubscribe (public) ─────────────────────────────────────────

@router.get("/unsubscribe")
async def unsubscribe(
    e: str = "",
    t: str = "",
):
    email = unquote(e).lower()
    if not email or _hmac_token(email) != t:
        return HTMLResponse("<h2>Invalid unsubscribe link.</h2>", status_code=400)

    for c in _contacts.values():
        if c.get("email") == email:
            c["unsubscribed"] = True
            c["status"] = "unsubscribed"
            break

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
):
    """Scrape a contact's website for email addresses."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    contact = _contacts.get(contact_id)
    if not contact:
        return JSONResponse({"error": "Not found"}, 404)

    if not contact.get("website"):
        return JSONResponse({"error": "No website URL on this contact"}, 400)

    result = await scrape_website_for_emails(contact["website"])

    had_email = bool(contact.get("email"))
    if result["emails"] and not had_email:
        contact["email"] = result["emails"][0]
        contact["source"] = contact.get("source") or "enriched"

    return {
        "contact_id": contact_id,
        "website": contact["website"],
        "emails_found": result["emails"],
        "pages_checked": result["pages_checked"],
        "auto_set": result["emails"][0] if result["emails"] and not had_email else None,
    }


@router.post("/api/enrich-batch")
async def enrich_batch(
    limit: int = Query(20),
    hiq_outreach: str | None = Cookie(None),
):
    """Scrape websites for contacts that have a website but no email."""
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    candidates = [
        c for c in _contacts.values()
        if c.get("website")
        and not c.get("email")
        and not c.get("unsubscribed")
        and c.get("enrich_status") not in ("enriched_no_email", "enrich_error")
    ]
    candidates = candidates[:limit]

    results = []
    for contact in candidates:
        try:
            result = await scrape_website_for_emails(contact["website"])
            if result["emails"]:
                contact["email"] = result["emails"][0]
                contact["enrich_status"] = "enriched"
                results.append({
                    "company": contact.get("company_name"),
                    "website": contact["website"],
                    "email": result["emails"][0],
                    "all_emails": result["emails"],
                })
            else:
                contact["enrich_status"] = "enriched_no_email"
                results.append({
                    "company": contact.get("company_name"),
                    "website": contact["website"],
                    "email": None,
                    "all_emails": [],
                })
        except Exception as e:
            contact["enrich_status"] = "enrich_error"
            results.append({
                "company": contact.get("company_name"),
                "website": contact["website"],
                "email": None,
                "error": str(e),
            })

    enriched = sum(1 for r in results if r.get("email"))
    return {"processed": len(results), "enriched": enriched, "results": results}


@router.post("/api/scrape-directory")
async def scrape_directory(
    source: str = Query("google"),
    query: str = Query("recruitment agency Australia"),
    hiq_outreach: str | None = Cookie(None),
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
        already_exists = any(
            (website and c.get("website") == website) or
            (email and c.get("email") == email)
            for c in _contacts.values()
        )
        if already_exists:
            skipped += 1
            continue

        cid = str(uuid.uuid4())
        _contacts[cid] = {
            "id": cid,
            "company_name": agency.get("company_name"),
            "contact_name": None,
            "email": email or None,
            "phone": None,
            "website": website or None,
            "location": agency.get("location", "Australia"),
            "industry": agency.get("industry", "general"),
            "role_type": "agency_director",
            "source": agency.get("source", source),
            "status": "not_started",
            "unsubscribed": False,
            "send_count": 0,
            "date_contacted": None,
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        created += 1

    return {"source": source, "found": len(agencies), "created": created, "skipped": skipped}


@router.post("/api/seed")
async def seed_from_csv(
    hiq_outreach: str | None = Cookie(None),
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
        already_exists = any(
            website and c.get("website") == website
            for c in _contacts.values()
        )
        if already_exists:
            skipped += 1
            continue

        cid = str(uuid.uuid4())
        _contacts[cid] = {
            "id": cid,
            "company_name": company or None,
            "contact_name": None,
            "email": None,
            "phone": None,
            "website": website or None,
            "location": (row.get("location") or "").strip() or "Australia",
            "industry": (row.get("industry") or "").strip() or "general",
            "role_type": (row.get("role_type") or "").strip() or "agency_director",
            "source": "au_agencies_csv",
            "status": "not_started",
            "unsubscribed": False,
            "send_count": 0,
            "date_contacted": None,
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        created += 1

    return {"total_in_csv": len(rows), "created": created, "skipped": skipped}


@router.post("/api/scrape-recruiters")
async def scrape_recruiters_from_agencies(
    limit: int = 10,
    hiq_outreach: str | None = Cookie(None),
):
    """Scrape team pages of seeded agencies to find individual recruiter names + emails.

    For each agency contact that has a website but no individual recruiter contacts,
    scrapes the team/people page for names, guesses emails from the domain.
    Creates new individual contacts linked to the agency.
    """
    if not _verify(hiq_outreach):
        return JSONResponse({"error": "Unauthorized"}, 401)

    from app.services.recruiter_scraper import scrape_agency_for_recruiters

    # Find agency contacts with websites that we haven't scraped yet
    agencies_to_scrape = []
    for cid, c in _contacts.items():
        if (
            c.get("website")
            and c.get("source") in ("au_agencies_csv", "google_search", "rcsa_directory")
            and not c.get("_recruiters_scraped")
        ):
            agencies_to_scrape.append((cid, c))
        if len(agencies_to_scrape) >= limit:
            break

    total_recruiters = 0
    agencies_processed = 0
    results = []

    for cid, agency in agencies_to_scrape:
        website = agency["website"]
        company = agency.get("company_name", "Unknown")

        try:
            recruiters = await scrape_agency_for_recruiters(website)

            for person in recruiters:
                name = person.get("contact_name", "")
                email = person.get("email")

                if not name:
                    continue

                # Skip if we already have this person
                already_exists = any(
                    c.get("contact_name") == name and c.get("company_name") == company
                    for c in _contacts.values()
                )
                if already_exists:
                    continue

                new_id = str(uuid.uuid4())
                _contacts[new_id] = {
                    "id": new_id,
                    "company_name": company,
                    "contact_name": name,
                    "email": email,
                    "phone": None,
                    "website": website,
                    "location": agency.get("location", "Australia"),
                    "industry": agency.get("industry", "general"),
                    "role_type": "recruiter",
                    "source": person.get("source", "team_page_scrape"),
                    "status": "not_started",
                    "unsubscribed": False,
                    "send_count": 0,
                    "date_contacted": None,
                    "notes": f"Guessed emails: {', '.join(person.get('guessed_emails', [])[:3])}" if person.get("guessed_emails") else None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                total_recruiters += 1

            # Mark this agency as scraped
            _contacts[cid]["_recruiters_scraped"] = True
            agencies_processed += 1

            results.append({
                "agency": company,
                "website": website,
                "recruiters_found": len(recruiters),
            })

        except Exception as e:
            logger.warning("Failed to scrape %s: %s", website, e)
            _contacts[cid]["_recruiters_scraped"] = True
            results.append({"agency": company, "website": website, "error": str(e)})

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
):
    if not _verify(hiq_outreach):
        return _unauth()

    # Fetch stats for KPI cards
    status_counts: dict[str, int] = {}
    for c in _contacts.values():
        s = c.get("status", "not_started")
        status_counts[s] = status_counts.get(s, 0) + 1
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
</div>

<div class="content">

<!-- CONTACTS TAB -->
<div id="tab-contacts" class="panel active">
<div class="kpis">{kpi_html}</div>

<div class="toolbar">
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
<thead><tr><th>Name</th><th>Company</th><th>Email</th><th>Website</th><th>Location</th><th>Industry</th><th>Status</th><th>Sends</th><th>Last Contacted</th><th>Actions</th></tr></thead>
<tbody id="contacts-body"></tbody>
</table>
</div>
</div>

<!-- ANALYTICS TAB -->
<div id="tab-analytics" class="panel">
<div id="stats-content"><p style="color:#64748b;">Loading...</p></div>
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

async function loadContacts(){{
  const industry=document.getElementById('f-industry').value;
  const status=document.getElementById('f-status').value;
  const search=document.getElementById('f-search').value;
  let qs='?limit=200';
  if(industry)qs+='&industry='+industry;
  if(status)qs+='&status='+status;
  if(search)qs+='&search='+encodeURIComponent(search);
  const data=await api('/contacts'+qs);
  const tbody=document.getElementById('contacts-body');
  tbody.innerHTML=data.contacts.map(c=>`<tr>
    <td>${{c.contact_name||'\u2014'}}</td>
    <td>${{c.company_name||'\u2014'}}</td>
    <td style="font-size:12px">${{c.email?`<span style="color:#4ade80">${{c.email}}</span>`:'<span style="color:#64748b;font-style:italic">no email</span>'}}</td>
    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{c.website?`<a href="${{c.website}}" target="_blank" style="color:#7c5cff;text-decoration:none">${{c.website.replace(/^https?:\/\/(www\.)?/,'')}}</a>`:'\u2014'}}</td>
    <td>${{c.location||'\u2014'}}</td>
    <td>${{c.industry||'\u2014'}}</td>
    <td><span class="badge badge-${{c.status}}">${{c.status}}</span></td>
    <td>${{c.send_count}}</td>
    <td style="font-size:11px;color:#64748b">${{c.date_contacted?new Date(c.date_contacted).toLocaleDateString():'\u2014'}}</td>
    <td style="white-space:nowrap">
      ${{c.email?`<button class="btn btn-sm btn-primary" onclick="sendTo('${{c.id}}',false)">Send</button>`:`<button class="btn btn-sm" style="background:#1a3a2a;color:#4ade80" onclick="enrichOne('${{c.id}}')">Enrich</button>`}}
      <button class="btn btn-sm" style="background:#2a2a40;color:#94a3b8" onclick="sendTo('${{c.id}}',true)">Test</button>
      <button class="btn btn-sm" style="background:#2a2a40;color:#94a3b8" onclick="editContact('${{c.id}}')">Edit</button>
      <button class="btn btn-sm btn-danger" onclick="deleteContact('${{c.id}}')">Del</button>
    </td>
  </tr>`).join('');
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
  const s=await api('/stats');
  const sc=s.status_counts||{{}};
  const eng=s.engagement||{{}};
  let html='<div class="kpis" style="margin-bottom:24px;">';
  html+='<div style="background:#111118;border-radius:12px;padding:16px 20px;border:1px solid #1e1e30;"><p style="color:#64748b;font-size:11px;text-transform:uppercase;">Opens (30d)</p><p style="color:#22c55e;font-size:24px;font-weight:700;">'+eng.opens+'</p></div>';
  html+='<div style="background:#111118;border-radius:12px;padding:16px 20px;border:1px solid #1e1e30;"><p style="color:#64748b;font-size:11px;text-transform:uppercase;">Clicks (30d)</p><p style="color:#3b82f6;font-size:24px;font-weight:700;">'+eng.clicks+'</p></div>';
  html+='</div>';
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

// Initial load
loadContacts();
</script>
</body></html>"""
