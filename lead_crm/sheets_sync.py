"""Append/refresh CRM rows in one fixed Google Sheet via a service account.

This is the in-session equivalent of the daily automation's Sheets writer:
point it at a service-account JSON and a sheet ID, and it appends new
Contacts (deduped by LinkedIn URL) to a single stable tracker — no new file
per run. Company sites are normalized to full https:// URLs so they're
clickable in the sheet.
"""

from .models import TRACKER_FIELDS, Contact

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def as_url(site: str) -> str:
    """Normalize a bare domain to a clickable https:// URL ('' stays '')."""
    site = (site or "").strip()
    if not site:
        return ""
    if site.startswith(("http://", "https://")):
        return site
    return "https://" + site


def open_worksheet(service_account_file: str, sheet_id: str):
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(service_account_file, scopes=_SCOPES)
    return gspread.authorize(creds).open_by_key(sheet_id).sheet1


def existing_linkedin_urls(ws) -> set[str]:
    col = TRACKER_FIELDS.index("linkedin_url") + 1
    return {v.strip().lower() for v in ws.col_values(col)[1:] if v.strip()}


def append_contacts(ws, contacts: list[Contact]) -> int:
    """Append contacts not already present (by LinkedIn URL). Returns count added."""
    if not ws.get_all_values():
        ws.append_row(TRACKER_FIELDS, value_input_option="RAW")
    seen = existing_linkedin_urls(ws)
    rows, added = [], set()
    for c in contacts:
        c.company_site = as_url(c.company_site)  # normalize to clickable https:// URL
        key = c.linkedin_url.strip().lower()
        if not key or key in seen or key in added:
            continue
        rows.append(c.as_row())
        added.add(key)
    if rows:
        ws.append_rows(rows, value_input_option="RAW")
    return len(rows)
