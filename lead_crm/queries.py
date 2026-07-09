"""Generate lane-tagged LinkedIn dork queries from the target config.

Query shape (per the discovery brief):
    site:linkedin.com/in ("TITLE1" OR "TITLE2" OR ...) "COMPANY"

Each generated item carries its lane and company so results can be tagged
without re-parsing. Titles are OR-grouped per company to keep the number of
searches (and therefore weekly usage) low.
"""

from dataclasses import dataclass

from .config import COMPANIES, Company, titles_for_lane


@dataclass
class DorkQuery:
    query: str
    company: str
    lane: str
    country: str
    company_site: str = ""
    source_method: str = "linkedin-dork"


def _or_group(titles: list[str]) -> str:
    return " OR ".join(f'"{t}"' for t in titles)


def build_query(company: Company, max_titles: int | None = None) -> DorkQuery:
    """One OR-grouped dork for a company (optionally cap titles for shorter queries)."""
    titles = titles_for_lane(company.lane)
    if max_titles:
        titles = titles[:max_titles]
    q = f'site:linkedin.com/in ({_or_group(titles)}) "{company.name}"'
    return DorkQuery(
        query=q,
        company=company.name,
        lane=company.lane,
        country=company.country,
        company_site=company.site,
    )


def build_all(companies: list[Company] | None = None, max_titles: int | None = None) -> list[DorkQuery]:
    """Build one dork per company in the target list."""
    return [build_query(c, max_titles=max_titles) for c in (companies or COMPANIES)]


def build_for_lane(lane_prefix: str, max_titles: int | None = None) -> list[DorkQuery]:
    """Build dorks for a lane, e.g. '1' for all of Lane 1, or '1A' for Tier A."""
    selected = [c for c in COMPANIES if c.lane.startswith(lane_prefix)]
    return [build_query(c, max_titles=max_titles) for c in selected]
