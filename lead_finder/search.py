"""Thin client for the Google Custom Search JSON API.

Docs: https://developers.google.com/custom-search/v1/overview
Free tier: 100 queries/day. Each API call returns up to 10 results ("one
page"); for LinkedIn dorks one page is almost always enough, so we default
to a single page per query to stretch the daily budget across more dorks.
"""

import logging

import requests

logger = logging.getLogger(__name__)

ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class SearchError(Exception):
    """Raised when the search API returns an unrecoverable error."""


class GoogleSearchClient:
    """Runs queries against the Custom Search API, tracking the daily budget."""

    def __init__(
        self,
        api_key: str,
        engine_id: str,
        daily_budget: int = 100,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ):
        self.api_key = api_key
        self.engine_id = engine_id
        self.daily_budget = daily_budget
        self.timeout = timeout
        self.session = session or requests.Session()
        self.calls_made = 0

    @property
    def budget_left(self) -> int:
        return self.daily_budget - self.calls_made

    def search(self, query: str, pages: int = 1) -> list[dict]:
        """Return result dicts ({'title','link','snippet'}) for one query.

        Stops early (and logs) if the daily budget is exhausted. Network/API
        errors on a single query are swallowed so one bad query can't abort
        the whole run.
        """
        results: list[dict] = []
        for page in range(pages):
            if self.budget_left <= 0:
                logger.warning("daily search budget exhausted; stopping")
                break
            params = {
                "key": self.api_key,
                "cx": self.engine_id,
                "q": query,
                "start": 1 + page * 10,  # API is 1-indexed, 10 results/page
                "num": 10,
            }
            self.calls_made += 1
            try:
                resp = self.session.get(ENDPOINT, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                logger.error("search request failed for %r: %s", query, exc)
                break
            if resp.status_code == 429:
                logger.warning("rate limited / quota hit on %r; stopping", query)
                break
            if resp.status_code >= 400:
                logger.error("search error %s for %r: %s", resp.status_code, query, resp.text[:200])
                break

            items = resp.json().get("items", [])
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            if len(items) < 10:
                break  # no further pages available
        return results
