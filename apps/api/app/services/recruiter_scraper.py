"""Australian recruiter directory scraper, team page scraper, and email guesser."""
import re
import logging
from urllib.parse import urlparse

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
_GENERIC_PREFIXES = {"info@", "contact@", "admin@", "hello@", "enquiries@", "support@", "office@", "mail@", "careers@", "jobs@", "recruitment@", "hr@"}

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Team page paths to scrape for individual recruiter names
_TEAM_PATHS = [
    "/team", "/our-team", "/people", "/our-people",
    "/consultants", "/our-consultants", "/meet-the-team",
    "/about/team", "/about/people", "/about-us/team",
    "/staff", "/our-staff", "/recruiters", "/our-recruiters",
]

# Common email patterns: (first, last, domain) -> email candidates
_EMAIL_PATTERNS = [
    "{first}.{last}@{domain}",         # john.smith@agency.com
    "{first}{last}@{domain}",          # johnsmith@agency.com
    "{first_initial}{last}@{domain}",  # jsmith@agency.com
    "{first}@{domain}",               # john@agency.com
    "{first}_{last}@{domain}",        # john_smith@agency.com
    "{first}-{last}@{domain}",        # john-smith@agency.com
    "{first_initial}.{last}@{domain}", # j.smith@agency.com
]


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


def is_generic_email(email: str) -> bool:
    """Check if an email is a generic address (info@, contact@, etc.)."""
    return any(email.lower().startswith(p) for p in _GENERIC_PREFIXES)


def extract_names_from_html(html: str) -> list[dict]:
    """Extract individual person names from team/people page HTML.

    Looks for common patterns:
    - <h2>John Smith</h2> or <h3>Jane Doe</h3>
    - <div class="name">John Smith</div>
    - <span class="team-member-name">John Smith</span>
    - <strong>John Smith</strong> followed by title text
    - JSON-LD Person schema
    """
    people = []
    seen_names = set()

    # Pattern 1: Headings (h2, h3, h4) that look like names (2-3 capitalized words)
    name_in_heading = re.findall(
        r'<h[2-4][^>]*>\s*(?:<[^>]*>)*\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*(?:<[^>]*>)*\s*</h[2-4]>',
        html
    )
    for name in name_in_heading:
        name = name.strip()
        if name not in seen_names and len(name) > 4 and len(name) < 40:
            seen_names.add(name)
            people.append({"name": name})

    # Pattern 2: Elements with name-related class/id attributes
    name_in_class = re.findall(
        r'class="[^"]*(?:name|member|consultant|recruiter|person)[^"]*"[^>]*>\s*(?:<[^>]*>)*\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*(?:<[^>]*>)*\s*</',
        html, re.IGNORECASE
    )
    for name in name_in_class:
        name = name.strip()
        if name not in seen_names and len(name) > 4 and len(name) < 40:
            seen_names.add(name)
            people.append({"name": name})

    # Pattern 3: <strong> or <b> tags with name-like content near job titles
    name_in_strong = re.findall(
        r'<(?:strong|b)[^>]*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*</(?:strong|b)>',
        html
    )
    for name in name_in_strong:
        name = name.strip()
        if name not in seen_names and len(name) > 4 and len(name) < 40:
            # Check it's not a section title by filtering common non-names
            lower = name.lower()
            if any(skip in lower for skip in [
                "about us", "our team", "contact us", "our values", "our mission",
                "read more", "learn more", "view all", "see more", "get started",
                "find out", "quick links", "privacy policy", "terms of",
            ]):
                continue
            seen_names.add(name)
            people.append({"name": name})

    # Pattern 4: JSON-LD Person schema
    jsonld_matches = re.findall(r'"@type"\s*:\s*"Person"[^}]*"name"\s*:\s*"([^"]+)"', html)
    for name in jsonld_matches:
        name = name.strip()
        if name not in seen_names and len(name) > 4:
            seen_names.add(name)
            people.append({"name": name})

    # Pattern 5: alt text on images that look like portrait photos
    alt_names = re.findall(
        r'<img[^>]*alt="([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"[^>]*>',
        html
    )
    for name in alt_names:
        name = name.strip()
        if name not in seen_names and len(name) > 4 and len(name) < 40:
            seen_names.add(name)
            people.append({"name": name})

    return people


def guess_emails(first_name: str, last_name: str, domain: str) -> list[str]:
    """Generate possible email addresses from name + domain."""
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    if not first or not last or not domain:
        return []

    # Clean domain
    domain = domain.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]

    first_initial = first[0]

    guesses = []
    for pattern in _EMAIL_PATTERNS:
        email = pattern.format(
            first=first, last=last, domain=domain,
            first_initial=first_initial,
        )
        guesses.append(email)

    return guesses


def pick_best_email(emails: list[str]) -> str | None:
    """From a list of emails, pick the best one (prefer personal over generic)."""
    personal = [e for e in emails if not is_generic_email(e)]
    if personal:
        return personal[0]
    return emails[0] if emails else None


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
        for path in ["/contact", "/contact-us", "/about", "/about-us"]:
            try:
                resp = await client.get(base + path, headers={"User-Agent": _USER_AGENT})
                if resp.status_code == 200:
                    emails.update(extract_emails_from_html(resp.text))
                    pages_checked.append(base + path)
            except Exception:
                continue

    return {"emails": sorted(emails), "pages_checked": pages_checked}


async def scrape_team_page(url: str) -> dict:
    """Scrape team/people pages for individual recruiter names and emails.

    Returns:
        {
            "people": [{"name": "John Smith", "email": "john.smith@agency.com" or None, "guessed_emails": [...]}],
            "emails_found": ["direct@emails.com"],
            "pages_checked": ["/team", "/our-team"],
        }
    """
    if not url.startswith("http"):
        url = "https://" + url

    base = url.rstrip("/")
    domain = urlparse(base).hostname or ""
    if domain.startswith("www."):
        domain = domain[4:]

    all_people = []
    all_emails = set()
    pages_checked = []
    seen_names = set()

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True, verify=False) as client:
        for path in _TEAM_PATHS:
            try:
                resp = await client.get(base + path, headers={"User-Agent": _USER_AGENT})
                if resp.status_code != 200:
                    continue

                html = resp.text
                pages_checked.append(base + path)

                # Extract emails directly found on page
                page_emails = extract_emails_from_html(html)
                all_emails.update(page_emails)

                # Extract names
                names = extract_names_from_html(html)
                for person in names:
                    name = person["name"]
                    if name in seen_names:
                        continue
                    seen_names.add(name)

                    parts = name.split()
                    first = parts[0] if parts else ""
                    last = parts[-1] if len(parts) > 1 else ""

                    # Try to find this person's email in the page emails
                    personal_email = None
                    for e in page_emails:
                        e_lower = e.lower()
                        if first.lower() in e_lower or last.lower() in e_lower:
                            personal_email = e
                            break

                    # Generate guessed emails
                    guessed = guess_emails(first, last, domain) if first and last else []

                    all_people.append({
                        "name": name,
                        "email": personal_email,
                        "guessed_emails": guessed,
                        "first_name": first,
                        "last_name": last,
                    })

            except Exception:
                continue

    return {
        "people": all_people,
        "emails_found": sorted(all_emails),
        "pages_checked": pages_checked,
        "domain": domain,
    }


async def scrape_agency_for_recruiters(url: str) -> list[dict]:
    """Full scrape: get individual recruiters from an agency website.

    Combines team page scraping, email extraction, and email guessing.
    Returns a list of individual recruiter contacts.
    """
    # First get any direct emails from the site
    email_result = await scrape_website_for_emails(url)
    direct_emails = email_result["emails"]

    # Then scrape team pages for names
    team_result = await scrape_team_page(url)
    people = team_result["people"]
    domain = team_result["domain"]

    contacts = []

    if people:
        # We found named people — create contacts for each
        for person in people:
            email = person.get("email")
            if not email and person.get("guessed_emails"):
                # Use the first guessed email (first.last@domain is most common)
                email = person["guessed_emails"][0]

            contacts.append({
                "contact_name": person["name"],
                "email": email,
                "guessed_emails": person.get("guessed_emails", []),
                "source": "team_page_scrape",
            })
    elif direct_emails:
        # No named people found, but we have emails — create contacts from emails
        for email in direct_emails:
            if is_generic_email(email):
                continue
            # Try to derive name from email
            local = email.split("@")[0]
            parts = re.split(r'[._\-]', local)
            name = " ".join(p.capitalize() for p in parts if len(p) > 1)

            contacts.append({
                "contact_name": name or email.split("@")[0],
                "email": email,
                "guessed_emails": [],
                "source": "email_scrape",
            })

    return contacts


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
                html = resp.text
                logger.info("RCSA directory page fetched (%d bytes)", len(html))
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
    search_url = f"https://www.google.com/search?q={query}&num={num}"

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(search_url, headers={"User-Agent": _USER_AGENT})
            if resp.status_code == 200:
                urls = re.findall(r'href="(https?://(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[^"]*)"', resp.text)
                seen = set()
                for url in urls:
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    if not domain_match:
                        continue
                    d = domain_match.group(1).lower()
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
