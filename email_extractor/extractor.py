"""Orchestrates crawling/parsing and turns raw text into EmailRecords."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import document_parser, email_patterns
from .models import EmailRecord, Mention, SkippedSource
from .web_crawler import RateLimiter, RobotsCache, crawl_site

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExtractionPipeline:
    """Accumulates deduplicated email records and skip reasons across runs."""

    def __init__(self):
        self._records: dict[str, EmailRecord] = {}
        self._skipped: list[SkippedSource] = []

    def _add_mention(self, email: str, origin: str, context: str, timestamp: str) -> None:
        key = email.lower()
        mention = Mention(origin=origin, context=context, timestamp=timestamp)
        if key in self._records:
            self._records[key].mentions.append(mention)
        else:
            self._records[key] = EmailRecord(
                email=key,
                is_role_based=email_patterns.is_role_based(key),
                mentions=[mention],
            )

    def add_skip(self, source: str, reason: str) -> None:
        self._skipped.append(SkippedSource(source=source, reason=reason, timestamp=_now()))
        logger.info("skipped %s: %s", source, reason)

    def ingest_text(self, text: str, origin: str) -> int:
        """Find emails in `text` and record them as coming from `origin`."""
        timestamp = _now()
        matches = email_patterns.find_emails(text)
        for match in matches:
            self._add_mention(match["email"], origin, match["context"], timestamp)
        return len(matches)

    def ingest_file(self, path: Path) -> None:
        try:
            text = document_parser.parse_file(path)
        except document_parser.DocumentParseError as exc:
            self.add_skip(str(path), str(exc))
            return
        found = self.ingest_text(text, str(path))
        logger.info("parsed %s: %d email(s) found", path, found)

    def ingest_site(
        self,
        url: str,
        session: requests.Session,
        rate_limiter: RateLimiter,
        robots: RobotsCache,
        timeout: float,
        max_pages: int,
    ) -> None:
        result = crawl_site(url, session, rate_limiter, robots, timeout, max_pages)
        for page_url, html, title in result.pages:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            text_parts = [soup.get_text(" ", strip=True)]
            for anchor in soup.find_all("a", href=True):
                if anchor["href"].lower().startswith("mailto:"):
                    text_parts.append(anchor["href"][len("mailto:"):])
            found = self.ingest_text(" ".join(text_parts), page_url)
            logger.info("crawled %s (%s): %d email(s) found", page_url, title, found)
        for skipped_url, reason in result.skipped:
            self.add_skip(skipped_url, reason)

    def records(self) -> list[EmailRecord]:
        return sorted(self._records.values(), key=lambda r: r.email)

    def skipped(self) -> list[SkippedSource]:
        return self._skipped
