"""Polite, narrow web crawling limited to obvious public contact pages.

Design constraints (see README "Compliance notes"):
  * robots.txt is always checked before fetching any URL.
  * At most one request per domain per `rate_limit` seconds.
  * Only the homepage plus a handful of "/contact", "/about", "/team"
    style pages are ever fetched -- this is not a general-purpose crawler.
"""

import time
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = (
    "EmailResearchBot/1.0 (+contact: your-email@example.com; "
    "purpose: public contact-info aggregation)"
)

# Path fragments that mark a page as a plausible public contact page.
CONTACT_KEYWORDS = ("contact", "about", "team", "get-in-touch", "reach-us")

# Candidate paths tried on every site regardless of what the homepage links to.
CANDIDATE_PATHS = (
    "",
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/about", "/about-us", "/about_us", "/aboutus",
    "/team", "/our-team", "/ourteam", "/meet-the-team",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RateLimiter:
    """Enforces a minimum delay between requests to the same domain."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last_request: dict[str, float] = {}

    def wait(self, domain: str) -> None:
        last = self._last_request.get(domain)
        if last is not None:
            elapsed = time.monotonic() - last
            remaining = self.min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[domain] = time.monotonic()


class RobotsCache:
    """Fetches and caches robots.txt parsers per domain."""

    def __init__(self, session: requests.Session, timeout: float, user_agent: str):
        self.session = session
        self.timeout = timeout
        self.user_agent = user_agent
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _get_parser(self, base_url: str) -> urllib.robotparser.RobotFileParser:
        parts = urllib.parse.urlsplit(base_url)
        domain = f"{parts.scheme}://{parts.netloc}"
        if domain not in self._parsers:
            parser = urllib.robotparser.RobotFileParser()
            robots_url = urllib.parse.urljoin(domain, "/robots.txt")
            try:
                resp = self.session.get(robots_url, timeout=self.timeout)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    # No robots.txt (or blocked) => treat as "allow all".
                    parser.parse([])
            except requests.RequestException:
                parser.parse([])
            self._parsers[domain] = parser
        return self._parsers[domain]

    def can_fetch(self, url: str) -> bool:
        parser = self._get_parser(url)
        return parser.can_fetch(self.user_agent, url)


class CrawlResult:
    def __init__(self):
        self.pages: list[tuple[str, str, str]] = []  # (url, html, title)
        self.skipped: list[tuple[str, str]] = []       # (url, reason)


def _same_domain(url: str, base_domain: str) -> bool:
    return urllib.parse.urlsplit(url).netloc == base_domain


def _discover_contact_links(html: str, base_url: str, base_domain: str) -> list[str]:
    """Pull same-domain links whose URL or anchor text looks contact-related."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(base_url, anchor["href"])
        href = href.split("#")[0]
        if not _same_domain(href, base_domain):
            continue
        haystack = (href + " " + anchor.get_text(" ", strip=True)).lower()
        if any(keyword in haystack for keyword in CONTACT_KEYWORDS):
            links.append(href)
    return links


def crawl_site(
    start_url: str,
    session: requests.Session,
    rate_limiter: RateLimiter,
    robots: RobotsCache,
    timeout: float,
    max_pages: int,
) -> CrawlResult:
    """Fetch the homepage plus a bounded set of contact/about/team pages."""
    result = CrawlResult()
    if not urllib.parse.urlsplit(start_url).scheme:
        start_url = "https://" + start_url
    if not urllib.parse.urlsplit(start_url).path:
        start_url += "/"  # keeps the "" candidate path resolving to a stable homepage URL

    parts = urllib.parse.urlsplit(start_url)
    base_domain = parts.netloc
    to_visit = list(dict.fromkeys(
        urllib.parse.urljoin(start_url, path) for path in CANDIDATE_PATHS
    ))
    visited: set[str] = set()
    discovered_extra: list[str] = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        if not robots.can_fetch(url):
            result.skipped.append((url, "disallowed by robots.txt"))
            continue

        rate_limiter.wait(base_domain)
        try:
            resp = session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            result.skipped.append((url, f"request error: {exc}"))
            continue

        if resp.status_code == 404:
            result.skipped.append((url, "404 not found"))
            continue
        if resp.status_code >= 400:
            result.skipped.append((url, f"HTTP {resp.status_code}"))
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type:
            result.skipped.append((url, f"non-HTML content-type: {content_type}"))
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else ""
        result.pages.append((url, resp.text, title))

        # Only the homepage is used to discover further contact-style links,
        # keeping the crawl to "obvious public contact pages" rather than a
        # full site traversal.
        if url == start_url or url.rstrip("/") == start_url.rstrip("/"):
            discovered_extra = _discover_contact_links(resp.text, url, base_domain)
            for link in discovered_extra:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)

    return result
