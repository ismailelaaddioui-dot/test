"""Write extraction results to CSV and JSON."""

import csv
import json
from pathlib import Path

from .models import EmailRecord, SkippedSource

SOURCE_SEPARATOR = " | "


def _record_to_row(record: EmailRecord) -> dict:
    return {
        "email": record.email,
        "is_role_based": record.is_role_based,
        "num_sources": len(record.mentions),
        "sources": SOURCE_SEPARATOR.join(m.origin for m in record.mentions),
        "sample_context": record.mentions[0].context,
        "first_seen": record.first_seen,
        "last_seen": record.last_seen,
    }


def write_emails_csv(records: list[EmailRecord], path: Path) -> None:
    fieldnames = [
        "email", "is_role_based", "num_sources", "sources",
        "sample_context", "first_seen", "last_seen",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_row(record))


def write_emails_json(records: list[EmailRecord], path: Path) -> None:
    payload = [
        {
            "email": record.email,
            "is_role_based": record.is_role_based,
            "first_seen": record.first_seen,
            "last_seen": record.last_seen,
            "mentions": [
                {"origin": m.origin, "context": m.context, "timestamp": m.timestamp}
                for m in record.mentions
            ],
        }
        for record in records
    ]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def write_skip_log(skipped: list[SkippedSource], path: Path) -> None:
    fieldnames = ["source", "reason", "timestamp"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for item in skipped:
            writer.writerow({
                "source": item.source,
                "reason": item.reason,
                "timestamp": item.timestamp,
            })
