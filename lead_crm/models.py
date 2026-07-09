"""CRM tracker schema and follow-up scheduling."""

from dataclasses import dataclass, field
from datetime import date, timedelta

# Output column order (Google Sheet header + row serialization).
TRACKER_FIELDS = [
    "name",
    "title",
    "company",
    "company_site",    # full https:// URL to the company/agency site
    "lane",            # 1A / 1B / 1C / 2 / 3
    "country",
    "source_method",   # how the contact was discovered
    "email",
    "email_verified",  # Y / N
    "linkedin_url",
    "date_added",
    "status",          # new / sent / opened / replied / warm / parked
    "last_contact",
    "next_touch_date",
    "notes",
]

# Valid pipeline statuses.
STATUSES = ("new", "sent", "opened", "replied", "warm", "parked")


@dataclass
class Contact:
    name: str
    title: str
    company: str
    lane: str
    company_site: str = ""
    country: str = ""
    source_method: str = ""
    email: str = ""
    email_verified: str = "N"
    linkedin_url: str = ""
    date_added: str = ""
    status: str = "new"
    last_contact: str = ""
    next_touch_date: str = ""
    notes: str = ""

    def as_row(self) -> list[str]:
        return [getattr(self, f) for f in TRACKER_FIELDS]


def compute_next_touch(status: str, from_date: date | None = None) -> str:
    """Follow-up date from a status, per the outreach rules.

    - opened (no reply): nudge in ~7-10 days -> +8 days
    - replied / warm: long-cycle nurture ~6-8 weeks -> +7 weeks
    - sent: check back in ~2 weeks if no open signal
    - new / parked: no scheduled touch (returns '')
    """
    base = from_date or date.today()
    offsets = {
        "sent": timedelta(days=14),
        "opened": timedelta(days=8),
        "replied": timedelta(weeks=7),
        "warm": timedelta(weeks=7),
    }
    delta = offsets.get(status)
    return (base + delta).isoformat() if delta else ""
