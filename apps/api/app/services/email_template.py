"""Email template config — defaults and builder for outreach emails."""
from __future__ import annotations
from urllib.parse import quote

DEFAULT_CONFIG = {
    # ── Brand ──
    "brand_name": "HireIQ",
    "brand_color": "#7c5cff",
    "brand_tagline": "Evidence-first hiring",
    "brand_tagline_bold": "Rank candidates in seconds",
    "website_url": "https://hireiq.domato.ai",
    "company_legal": "A Domato AI product &bull; ABN 94 695 794 346",

    # ── Greeting ──
    "greeting_template": "Hi {first_name},",
    "intro_template": "I know {company} handles a lot of hiring. I wanted to show you something that could genuinely save your team hours every week.",

    # ── Pain points (per industry) ──
    "pain_points": {
        "tech": {
            "headline": "Screening 50 developer resumes for one role shouldn&rsquo;t take a full day",
            "detail": "Technical skills, frameworks, and years of experience buried across inconsistent CV formats &mdash; it adds up fast.",
        },
        "healthcare": {
            "headline": "Healthcare credentials and compliance checks buried across resumes",
            "detail": "Certifications, licensure, and specialisations scattered across 30+ applications &mdash; one missed detail can cost you.",
        },
        "finance": {
            "headline": "Regulatory experience and certifications scattered across 30+ CVs",
            "detail": "CFA, Series exams, compliance history &mdash; finding qualified candidates means reading every line of every resume.",
        },
        "agency": {
            "headline": "Your clients expect shortlists in hours, not days",
            "detail": "Multiple roles, multiple clients, hundreds of resumes. Manual screening kills your margins.",
        },
        "general": {
            "headline": "Still reading every resume top to bottom?",
            "detail": "When you&rsquo;re hiring for multiple roles, manual screening doesn&rsquo;t scale.",
        },
    },

    # ── Solution section ──
    "solution_text": "<strong style=\"color:#e2e8f0;\">HireIQ ranks candidates against your job description in 30 seconds.</strong> Paste a JD, drop resumes, get an evidence-backed shortlist.",

    # ── Feature cards (6 items, icon + title + description) ──
    "features": [
        {"icon": "&#128203;", "title": "Paste any JD", "desc": "Instant criteria extraction &mdash; skills, experience, qualifications auto-detected."},
        {"icon": "&#128196;", "title": "Drop Resumes", "desc": "AI reads every line of every CV &mdash; PDF, DOCX, any format."},
        {"icon": "&#127919;", "title": "8-Factor Scoring", "desc": "Evidence for every match &mdash; no black-box rankings."},
        {"icon": "&#9878;&#65039;", "title": "Side-by-Side Compare", "desc": "Compare candidates head-to-head. Decide faster."},
        {"icon": "&#128269;", "title": "Skills Gap Analysis", "desc": "Know exactly what each candidate is missing before the interview."},
        {"icon": "&#10024;", "title": "Recruiter Summary", "desc": "AI-generated candidate brief &mdash; save hours per role."},
    ],

    # ── KPI row ──
    "kpis": [
        {"icon": "&#9889;", "value": "30s", "label": "Per Role"},
        {"icon": "&#127919;", "value": "8", "label": "Score Factors"},
        {"icon": "&#128202;", "value": "100%", "label": "Evidence-Backed"},
    ],

    # ── CTA block ──
    "cta_headline": "Stop screening. Start shortlisting.",
    "cta_subtext": "Rank every candidate against your JD &mdash; free to start.",
    "cta_button_text": "Try HireIQ Free &rarr;",
    "cta_fine_print": "No credit card &bull; Unlimited JDs &bull; Free tier included",

    # ── Secondary actions ──
    "secondary_links": [
        {"icon": "&#128218;", "label": "Features"},
        {"icon": "&#128179;", "label": "Pricing"},
    ],

    # ── Sign-off ──
    "signoff_line1": "Cheers,",
    "signoff_line2": "The HireIQ Team",

    # ── Subject line ──
    "subject_template": "Stop spending hours screening resumes \u2014 {contact_name}",

    # ── Colors (advanced) ──
    "colors": {
        "bg": "#0a0a0a",
        "card_bg": "#111118",
        "header_gradient": "linear-gradient(135deg,#0a0a14 0%,#12121f 50%,#1a1a30 100%)",
        "accent": "#7c5cff",
        "text_primary": "#e2e8f0",
        "text_secondary": "#c4c4d4",
        "text_muted": "#94a3b8",
        "text_faint": "#64748b",
        "border": "#2a2a40",
        "feature_bg": "#13132a",
        "feature_border": "#2a2a45",
        "pain_bg": "#1a1528",
        "cta_gradient": "linear-gradient(135deg,#1a1040 0%,#251650 100%)",
        "cta_border": "#3a2a60",
        "footer_bg": "#0a0a14",
    },
}


def get_config_with_defaults(saved_config: dict | None) -> dict:
    """Merge saved config over defaults (shallow per top-level key)."""
    if not saved_config:
        return DEFAULT_CONFIG.copy()
    merged = DEFAULT_CONFIG.copy()
    for key, value in saved_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def build_email_html(contact: dict, config: dict, backend_url: str) -> str:
    """Build the outreach email HTML from config and contact data."""
    name = contact.get("contact_name") or "there"
    first = name.split()[0] if name != "there" else "there"
    company = contact.get("company_name") or "your team"
    industry = (contact.get("industry") or "general").lower()
    email = contact.get("email", "")
    colors = config.get("colors", DEFAULT_CONFIG["colors"])
    website = config.get("website_url", DEFAULT_CONFIG["website_url"])

    def tracked(url):
        return f"{backend_url}/r?u={quote(url, safe='')}&e={quote(email, safe='')}"

    def unsub():
        import hashlib, hmac as hmac_mod
        secret = "outreach-dev-secret"  # Will be overridden by caller
        token = hmac_mod.new(secret.encode(), email.lower().encode(), hashlib.sha256).hexdigest()[:16]
        return f"{backend_url}/api/admin/outreach/unsubscribe?e={quote(email, safe='')}&t={token}"

    # Pain point
    pain_points = config.get("pain_points", DEFAULT_CONFIG["pain_points"])
    h = pain_points.get(industry, pain_points.get("general", DEFAULT_CONFIG["pain_points"]["general"]))

    # Greeting
    greeting = config.get("greeting_template", DEFAULT_CONFIG["greeting_template"]).replace("{first_name}", first)
    intro = config.get("intro_template", DEFAULT_CONFIG["intro_template"]).replace("{company}", company)

    # Subject (returned separately)
    # Features
    features = config.get("features", DEFAULT_CONFIG["features"])
    features_html = ""
    for i in range(0, len(features), 2):
        features_html += '<tr>'
        for f in features[i:i+2]:
            features_html += f'''<td style="width:50%;padding:14px;background:{colors.get("feature_bg","#13132a")};border-radius:8px;border:1px solid {colors.get("feature_border","#2a2a45")};vertical-align:top;">
<div style="font-size:18px;margin-bottom:6px;">{f["icon"]}</div>
<div style="font-size:13px;font-weight:700;color:{colors.get("text_primary","#e2e8f0")};margin-bottom:3px;">{f["title"]}</div>
<div style="font-size:12px;color:{colors.get("text_muted","#94a3b8")};line-height:1.4;">{f["desc"]}</div>
</td>'''
        features_html += '</tr>'

    # KPIs
    kpis = config.get("kpis", DEFAULT_CONFIG["kpis"])
    kpi_html = '<table role="presentation" cellpadding="0" cellspacing="6" width="100%"><tr>'
    for k in kpis:
        kpi_html += f'''<td style="padding:14px;text-align:center;background:#161625;border-radius:8px;width:33%;border:1px solid {colors.get("border","#2a2a40")};">
<div style="font-size:22px;margin-bottom:4px;">{k["icon"]}</div>
<div style="font-size:20px;font-weight:700;color:{colors.get("text_primary","#e2e8f0")};">{k["value"]}</div>
<div style="font-size:11px;color:{colors.get("text_muted","#94a3b8")};margin-top:2px;text-transform:uppercase;letter-spacing:0.04em;">{k["label"]}</div></td>'''
    kpi_html += '</tr></table>'

    # Secondary links
    sec_links = config.get("secondary_links", DEFAULT_CONFIG["secondary_links"])
    sec_html = ""
    for sl in sec_links:
        sec_html += f'''<td style="width:50%;text-align:center;background:#161625;border-radius:8px;padding:14px 12px;border:1px solid {colors.get("border","#2a2a40")};">
<a href="{tracked(website)}" style="text-decoration:none;">
<span style="display:block;font-size:18px;margin-bottom:4px;">{sl["icon"]}</span>
<span style="font-size:12px;font-weight:600;color:{colors.get("text_primary","#e2e8f0")};">{sl["label"]}</span>
</a></td>'''

    accent = colors.get("accent", "#7c5cff")
    brand = config.get("brand_name", "HireIQ")
    signup_url = tracked(f"{website}?ref=outreach")

    return f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:{colors.get("bg","#0a0a0a")};">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:{colors.get("bg","#0a0a0a")};">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width:600px;width:100%;background-color:{colors.get("card_bg","#111118")};border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.5);">

<!-- Header -->
<tr><td style="background:{colors.get("header_gradient","linear-gradient(135deg,#0a0a14 0%,#12121f 50%,#1a1a30 100%)")};padding:28px 32px 20px;border-bottom:1px solid {colors.get("border","#2a2a40")};">
<a href="{tracked(website)}" style="text-decoration:none;">
<span style="font-size:24px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;">{brand.replace("IQ","")}</span><span style="font-size:24px;font-weight:700;color:{accent};letter-spacing:-0.02em;">{"IQ" if "IQ" in brand else ""}</span>
</a>
<p style="margin:8px 0 0;font-size:13px;color:{colors.get("text_muted","#94a3b8")};">{config.get("brand_tagline",DEFAULT_CONFIG["brand_tagline"])} &bull; <strong style="color:{colors.get("text_primary","#e2e8f0")};">{config.get("brand_tagline_bold",DEFAULT_CONFIG["brand_tagline_bold"])}</strong></p>
</td></tr>

<!-- Greeting -->
<tr><td style="padding:28px 32px 12px;">
<p style="margin:0 0 14px;color:{colors.get("text_primary","#e2e8f0")};font-size:15px;font-weight:500;">{greeting}</p>
<p style="margin:0 0 14px;color:{colors.get("text_secondary","#c4c4d4")};font-size:14px;line-height:1.6;">{intro}</p>
</td></tr>

<!-- Pain point -->
<tr><td style="padding:0 32px 16px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
<tr><td style="padding:14px 18px;background:{colors.get("pain_bg","#1a1528")};border-left:4px solid {accent};border-radius:0 8px 8px 0;">
<p style="margin:0;color:#c4b5fd;font-size:13px;line-height:1.5;font-style:italic;">{h["headline"]}</p>
<p style="margin:8px 0 0;color:{colors.get("text_muted","#94a3b8")};font-size:12px;line-height:1.5;">{h["detail"]}</p>
</td></tr></table>
</td></tr>

<!-- Solution -->
<tr><td style="padding:0 32px 8px;">
<p style="margin:0;color:{colors.get("text_secondary","#c4c4d4")};font-size:14px;line-height:1.6;">{config.get("solution_text",DEFAULT_CONFIG["solution_text"])}</p>
</td></tr>

<!-- Features -->
<tr><td style="padding:8px 32px;">
<table role="presentation" cellpadding="0" cellspacing="8" width="100%">
{features_html}
</table></td></tr>

<!-- KPIs -->
<tr><td style="padding:12px 32px 4px;">{kpi_html}</td></tr>

<!-- CTA -->
<tr><td style="padding:16px 32px 8px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:{colors.get("cta_gradient","linear-gradient(135deg,#1a1040 0%,#251650 100%)")};border-radius:10px;overflow:hidden;border:1px solid {colors.get("cta_border","#3a2a60")};">
<tr><td style="padding:24px;text-align:center;">
<p style="margin:0 0 6px;color:#ffffff;font-size:16px;font-weight:700;">{config.get("cta_headline",DEFAULT_CONFIG["cta_headline"])}</p>
<p style="margin:0 0 16px;color:{colors.get("text_muted","#94a3b8")};font-size:13px;">{config.get("cta_subtext",DEFAULT_CONFIG["cta_subtext"])}</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
<a href="{signup_url}" style="display:inline-block;background:{accent};color:#ffffff;font-size:14px;font-weight:700;padding:14px 32px;border-radius:8px;text-decoration:none;">{config.get("cta_button_text",DEFAULT_CONFIG["cta_button_text"])}</a>
</td></tr></table>
<p style="margin:10px 0 0;color:{colors.get("text_faint","#64748b")};font-size:11px;">{config.get("cta_fine_print",DEFAULT_CONFIG["cta_fine_print"])}</p>
</td></tr></table>
</td></tr>

<!-- Secondary -->
<tr><td style="padding:8px 32px;">
<table role="presentation" cellpadding="0" cellspacing="8" width="100%"><tr>
{sec_html}
</tr></table></td></tr>

<!-- Sign-off -->
<tr><td style="padding:16px 32px 20px;">
<p style="margin:0 0 4px;color:{colors.get("text_primary","#e2e8f0")};font-size:14px;">{config.get("signoff_line1",DEFAULT_CONFIG["signoff_line1"])}</p>
<p style="margin:0;color:{colors.get("text_primary","#e2e8f0")};font-size:14px;font-weight:600;">{config.get("signoff_line2",DEFAULT_CONFIG["signoff_line2"])}</p>
<p style="margin:2px 0 0;color:#6b7280;font-size:12px;"><a href="{tracked(website)}" style="color:{accent};text-decoration:none;">hireiq.domato.ai</a></p>
</td></tr>

<!-- Footer -->
<tr><td style="padding:16px 32px;background-color:{colors.get("footer_bg","#0a0a14")};border-top:1px solid #1e1e30;">
<p style="margin:0 0 6px;color:{colors.get("text_faint","#64748b")};font-size:11px;"><a href="{tracked(website)}" style="color:{accent};text-decoration:none;font-weight:600;">{brand}</a> &mdash; {config.get("company_legal",DEFAULT_CONFIG["company_legal"])}</p>
<p style="margin:6px 0 0;font-size:11px;">
<a href="{tracked(website + '/contact')}" style="color:{accent};text-decoration:none;">Contact Us</a>
<span style="color:#333;"> &bull; </span>
<a href="{backend_url}/api/admin/outreach/unsubscribe?e={quote(email, safe='')}&t=__UNSUB_TOKEN__" style="color:{colors.get("text_faint","#64748b")};text-decoration:none;">Unsubscribe</a>
<span style="color:#333;"> &bull; </span>
<a href="{tracked(website + '/privacy')}" style="color:{colors.get("text_faint","#64748b")};text-decoration:none;">Privacy</a>
<span style="color:#333;"> &bull; </span>
<a href="{tracked(website + '/terms')}" style="color:{colors.get("text_faint","#64748b")};text-decoration:none;">Terms</a>
</p>
</td></tr>

</table></td></tr></table>
<img src="{backend_url}/o?e={quote(email, safe='')}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;border:0;" />
</body></html>'''


def build_subject(contact: dict, config: dict) -> str:
    """Build the email subject line from config."""
    template = config.get("subject_template", DEFAULT_CONFIG["subject_template"])
    name = contact.get("contact_name") or "you"
    return template.replace("{contact_name}", name)
