"""Australian recruiter directory scraper and email enrichment."""
import re
import logging
import httpx

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

_IGNORE_DOMAINS = {
    "example.com", "example.org", "sentry.io", "wixpress.com",
    "googleapis.com", "w3.org", "schema.org", "wordpress.org",
    "gravatar.com", "wp.com", "jquery.com", "google.com",
    "facebook.com", "twitter.com", "linkedin.com", "instagram.com",
    "cloudflare.com", "amazonaws.com", "microsoft.com",
}

_IGNORE_PREFIXES = {"noreply@", "no-reply@", "mailer-daemon@", "postmaster@", "webmaster@"}

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def extract_emails_from_html(html: str) -> list[str]:
    """Extract real email addresses from HTML, filtering junk."""
    raw = set(_EMAIL_RE.findall(html))
    clean = []
    for e in raw:
        e = e.lower().strip(".")
        domain = e.split("@", 1)[1] if "@" in e else ""
        if domain in _IGNORE_DOMAINS:
            continue
        if any(e.startswith(p) for p in _IGNORE_PREFIXES):
            continue
        if domain.endswith((".png", ".jpg", ".gif", ".css", ".js", ".svg")):
            continue
        clean.append(e)
    return sorted(set(clean))


async def scrape_website_for_emails(url: str) -> dict:
    """Scrape a website's homepage + contact pages for email addresses."""
    if not url.startswith("http"):
        url = "https://" + url

    emails = set()
    pages_checked = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True, verify=False) as client:
        # Homepage
        try:
            resp = await client.get(url, headers={"User-Agent": _USER_AGENT})
            if resp.status_code == 200:
                emails.update(extract_emails_from_html(resp.text))
                pages_checked.append(url)
        except Exception:
            pass

        # Contact pages
        base = url.rstrip("/")
        for path in ["/contact", "/contact-us", "/about", "/about-us", "/team", "/people", "/our-team"]:
            try:
                resp = await client.get(base + path, headers={"User-Agent": _USER_AGENT})
                if resp.status_code == 200:
                    emails.update(extract_emails_from_html(resp.text))
                    pages_checked.append(base + path)
            except Exception:
                continue

    return {"emails": sorted(emails), "pages_checked": pages_checked}


async def scrape_rcsa_directory() -> list[dict]:
    """Scrape RCSA member directory for recruitment agencies."""
    results = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(
                "https://www.rcsa.com.au/Web/Find-a-Member",
                headers={"User-Agent": _USER_AGENT}
            )
            if resp.status_code == 200:
                # Extract agency names, locations, websites from the directory HTML
                # RCSA uses a member search — try to extract what we can from the page
                html = resp.text
                # Look for member listing patterns
                # This may need adjustment based on actual page structure
                logger.info("RCSA directory page fetched (%d bytes)", len(html))
                # Extract any emails found on the page
                emails = extract_emails_from_html(html)
                if emails:
                    for email in emails:
                        results.append({
                            "company_name": email.split("@")[1].split(".")[0].title(),
                            "email": email,
                            "website": f"https://{email.split('@')[1]}",
                            "location": "Australia",
                            "industry": "general",
                            "source": "rcsa_directory",
                        })
        except Exception as e:
            logger.warning("RCSA scrape failed: %s", e)

    return results


async def google_search_agencies(query: str, num: int = 20) -> list[dict]:
    """Search Google for recruitment agency websites."""
    results = []
    # Use Google search to find agency websites
    search_url = f"https://www.google.com/search?q={query}&num={num}"

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(search_url, headers={"User-Agent": _USER_AGENT})
            if resp.status_code == 200:
                # Extract URLs from Google results
                urls = re.findall(r'href="(https?://(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[^"]*)"', resp.text)
                seen = set()
                for url in urls:
                    # Filter out Google/social media URLs
                    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    if not domain:
                        continue
                    d = domain.group(1).lower()
                    if any(skip in d for skip in ["google.", "youtube.", "facebook.", "linkedin.", "twitter.", "instagram.", "wikipedia.", "reddit."]):
                        continue
                    if d not in seen:
                        seen.add(d)
                        results.append({
                            "company_name": d.replace(".com.au", "").replace(".com", "").replace("-", " ").title(),
                            "website": f"https://{d}",
                            "location": "Australia",
                            "industry": "general",
                            "source": "google_search",
                        })
        except Exception as e:
            logger.warning("Google search failed: %s", e)

    return results
