"""Append new leads to a Google Sheet, deduplicated by LinkedIn URL.

The Sheet itself is the dedup store: before appending we read the existing
LinkedIn-URL column and skip anyone already present. Auth uses a Google
service account (unattended, works from GitHub Actions).
"""

import json
import logging

from .models import FIELDS, Lead

logger = logging.getLogger(__name__)

# gspread/google-auth are only needed when actually writing to Sheets, so the
# rest of the package (and its tests) can import without them installed.
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetWriter:
    """Opens a worksheet and appends de-duplicated Lead rows."""

    def __init__(self, worksheet):
        self.worksheet = worksheet

    @classmethod
    def from_service_account(cls, service_account_info: dict, sheet_id: str):
        """Build a writer from a service-account dict and a spreadsheet ID."""
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(service_account_info, scopes=_SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        return cls(worksheet)

    def _ensure_header(self) -> None:
        """Write the header row if the sheet is empty."""
        existing = self.worksheet.get_all_values()
        if not existing:
            self.worksheet.append_row(FIELDS, value_input_option="RAW")

    def existing_linkedin_urls(self) -> set[str]:
        """LinkedIn URLs already in the sheet (lowercased), for dedup."""
        try:
            col = FIELDS.index("linkedin_url") + 1  # gspread columns are 1-indexed
            values = self.worksheet.col_values(col)
        except Exception as exc:  # empty sheet or transient read error
            logger.warning("could not read existing URLs: %s", exc)
            return set()
        return {v.strip().lower() for v in values[1:] if v.strip()}  # skip header

    def append_new(self, leads: list[Lead]) -> int:
        """Append leads whose LinkedIn URL isn't already present. Returns count added."""
        self._ensure_header()
        seen = self.existing_linkedin_urls()

        rows, added_urls = [], set()
        for lead in leads:
            key = lead.linkedin_url.strip().lower()
            if not key or key in seen or key in added_urls:
                continue
            rows.append(lead.as_row())
            added_urls.add(key)

        if rows:
            self.worksheet.append_rows(rows, value_input_option="RAW")
        return len(rows)


def load_service_account(raw: str) -> dict:
    """Parse service-account JSON from a string (env var or file contents)."""
    return json.loads(raw)
