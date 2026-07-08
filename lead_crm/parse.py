"""Turn a LinkedIn /in/ result into a CRM Contact, or reject it.

Reuses the same filtering ideas as `lead_finder`: only real profile URLs,
outlet/company must actually appear in the result. Adds CRM enrichment:
lane tagging (from the originating query), country inference, Morocco-client
exclusion, and initial status/date fields.
"""

import re
from datetime import date

from .config import is_excluded_client
from .models import Contact

_PROFILE_RE = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/", re.IGNORECASE)
_NOISE_PATH = ("/jobs/", "/posts/", "/pulse/", "/company/", "/school/")
_TITLE_TAIL_RE = re.compile(r"\s*[|\-–]\s*linkedin\s*$", re.IGNORECASE)

# LinkedIn country subdomains -> country label (best-effort fallback).
_SUBDOMAIN_COUNTRY = {
    "uk": "UK", "ae": "UAE", "fr": "France", "de": "Germany",
    "it": "Italy", "es": "Spain", "au": "Australia", "ca": "Canada",
    "in": "India", "nl": "Netherlands", "ma": "Morocco",
}


def is_profile_url(url: str) -> bool:
    if any(fragment in url.lower() for fragment in _NOISE_PATH):
        return False
    return bool(_PROFILE_RE.match(url))


def _country_from_url(url: str) -> str:
    match = re.match(r"^https?://([a-z]{2,3})\.linkedin\.com/", url, re.IGNORECASE)
    if match:
        return _SUBDOMAIN_COUNTRY.get(match.group(1).lower(), "")
    return ""


def _split_title(raw_title: str) -> tuple[str, str]:
    """Parse "Name - Title[ at Company]" -> (name, title)."""
    cleaned = _TITLE_TAIL_RE.sub("", raw_title).strip()
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if not parts:
        return "", ""
    name = parts[0]
    title = parts[1] if len(parts) >= 2 else ""
    if " at " in title.lower():
        title = title[: title.lower().index(" at ")].strip()
    return name, title


def parse_result(
    result: dict,
    company: str,
    lane: str,
    country: str,
    source_method: str = "linkedin-dork",
    is_morocco_fixer: bool = False,
    today: date | None = None,
) -> Contact | None:
    """Build a Contact from a search result, or None if it's noise/excluded."""
    if is_excluded_client(country, is_morocco_fixer):
        return None

    url = (result.get("link") or "").strip()
    if not is_profile_url(url):
        return None

    raw_title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    name, title = _split_title(raw_title)
    if not name:
        return None

    # The company must actually appear in the result, else it's a mismatch.
    haystack = f"{raw_title}\n{snippet}".lower()
    if company.lower() not in haystack:
        return None

    return Contact(
        name=name,
        title=title,
        company=company,
        lane=lane,
        country=country or _country_from_url(url),
        source_method=source_method,
        linkedin_url=url.split("?")[0],
        date_added=(today or date.today()).isoformat(),
        status="new",
    )
