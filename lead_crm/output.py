"""Serialize Contacts to CSV in the tracker schema."""

import csv
import io

from .models import TRACKER_FIELDS, Contact


def to_csv(contacts: list[Contact]) -> str:
    """Return a CSV string (header + rows) in TRACKER_FIELDS order."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(TRACKER_FIELDS)
    for c in contacts:
        writer.writerow(c.as_row())
    return buf.getvalue()


def dedupe(contacts: list[Contact]) -> list[Contact]:
    """Drop duplicates by LinkedIn URL (first occurrence wins)."""
    seen, out = set(), []
    for c in contacts:
        key = c.linkedin_url.strip().lower()
        if key and key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
