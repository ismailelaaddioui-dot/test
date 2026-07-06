"""Shared data structures."""

from dataclasses import dataclass

# Column order used everywhere (Sheet header + row serialization).
FIELDS = [
    "name",
    "title",
    "company",
    "company_site",
    "linkedin_url",
    "query",
    "found_date",
]


@dataclass
class Lead:
    """One prospect parsed from a search result."""

    name: str
    title: str
    company: str
    company_site: str
    linkedin_url: str
    query: str
    found_date: str

    def as_row(self) -> list[str]:
        """Serialize to a spreadsheet row in FIELDS order."""
        return [getattr(self, field) for field in FIELDS]
