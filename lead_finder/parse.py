"""Turn a raw Google result into a clean Lead, or reject it as noise.

LinkedIn profile result titles follow predictable shapes, e.g.:
    "Sam Brogan - Art Director at Monocle"
    "Erin Aulov - Senior Visuals Editor - POLITICO | LinkedIn"
We parse Name / Title / Company from those, then apply the filters we
validated by hand:
  * keep only real profile URLs (linkedin.com/in/...),
  * drop job listings, posts, articles, and company pages,
  * require the query's outlet/anchor to actually appear in the result,
    which throws out mismatches like film/TV "director of photography" hits.
"""

import re

from .domains import resolve_domain
from .models import Lead

# Only individual profiles. Everything else on linkedin.com is noise for us.
_PROFILE_RE = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/", re.IGNORECASE)

# URL fragments that mark a non-profile result (jobs, posts, articles, orgs).
_NOISE_PATH = ("/jobs/", "/posts/", "/pulse/", "/company/", "/school/", "/showcase/")

# Trailing site branding to strip from result titles before parsing.
_TITLE_TAIL_RE = re.compile(r"\s*[|\-–]\s*linkedin\s*$", re.IGNORECASE)


def _extract_quoted(query: str) -> list[str]:
    """Return the quoted phrases in a dork, e.g. ['photo editor', 'Monocle']."""
    return re.findall(r'"([^"]+)"', query)


def query_anchor(query: str) -> str:
    """The outlet/city/context term a query is anchored on (last quoted phrase)."""
    quoted = _extract_quoted(query)
    return quoted[-1] if quoted else ""


def is_profile_url(url: str) -> bool:
    """True only for individual LinkedIn profile URLs."""
    if any(fragment in url.lower() for fragment in _NOISE_PATH):
        return False
    return bool(_PROFILE_RE.match(url))


def _split_title(raw_title: str) -> tuple[str, str, str]:
    """Parse "Name - Title - Company" (and "Title at Company" variants).

    Returns (name, title, company); any piece may be '' if not present.
    """
    cleaned = _TITLE_TAIL_RE.sub("", raw_title).strip()
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if not parts:
        return "", "", ""

    name = parts[0]
    title, company = "", ""

    if len(parts) >= 3:
        # "Name - Title - Company [- Location]"
        title, company = parts[1], parts[2]
    elif len(parts) == 2:
        # "Name - Title at Company" or "Name - Company"
        second = parts[1]
        if " at " in second.lower():
            idx = second.lower().index(" at ")
            title, company = second[:idx].strip(), second[idx + 4:].strip()
        else:
            company = second

    # A trailing "at Company" can also hide inside the title slot.
    if title and not company and " at " in title.lower():
        idx = title.lower().index(" at ")
        title, company = title[:idx].strip(), title[idx + 4:].strip()

    return name, title, company


def parse_result(
    result: dict,
    query: str,
    found_date: str,
) -> Lead | None:
    """Build a Lead from one search result, or None if it should be dropped.

    `result` is a dict with at least 'title', 'link', and (optionally) 'snippet'.
    """
    url = (result.get("link") or "").strip()
    if not is_profile_url(url):
        return None

    raw_title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    name, parsed_title, parsed_company = _split_title(raw_title)
    if not name:
        return None

    anchor = query_anchor(query)
    haystack = f"{raw_title}\n{snippet}".lower()

    # Verify the query's anchor (outlet/city) actually appears in the result.
    # This is what removes cross-topic noise (e.g. a film DoP surfacing on a
    # magazine query): if the outlet isn't mentioned, it's not our person.
    if anchor and anchor.lower() not in haystack:
        return None

    # Prefer the known outlet as the company when the anchor is one we track;
    # otherwise fall back to whatever we parsed out of the title.
    if resolve_domain(anchor):
        company = anchor
    else:
        company = parsed_company

    return Lead(
        name=name,
        title=parsed_title,
        company=company,
        company_site=resolve_domain(company),
        linkedin_url=url.split("?")[0],  # strip tracking params
        query=query,
        found_date=found_date,
    )
