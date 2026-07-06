"""Command-line entry point: run today's slice and append new leads.

Reads config from CLI flags, with credentials taken from environment
variables (so GitHub Actions can inject them from secrets). A `--dry-run`
mode prints results instead of writing to Sheets and needs no credentials,
which is handy for local testing.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .parse import parse_result
from .rotation import load_queries, slice_for_day
from .search import GoogleSearchClient
from .sheets import SheetWriter, load_service_account

logger = logging.getLogger(__name__)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Find magazine/agency photo-desk contacts on LinkedIn via Google dorks."
    )
    parser.add_argument(
        "--queries-file", type=Path, default=Path("queries.txt"),
        help="File of dork queries, one per line (default: queries.txt).",
    )
    parser.add_argument(
        "--slice-size", type=int, default=90,
        help="How many queries to run today (default: 90, under the 100/day free cap).",
    )
    parser.add_argument(
        "--pages", type=int, default=1,
        help="Result pages per query, 10 results each (default: 1).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print leads instead of writing to Google Sheets (no credentials needed).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Debug logging.",
    )
    return parser.parse_args(argv)


def collect_leads(queries, client, pages):
    """Run each query, parse results, and return a de-duplicated list of Leads."""
    found_date = datetime.now(timezone.utc).date().isoformat()
    leads, seen = [], set()
    for query in queries:
        results = client.search(query, pages=pages)
        kept = 0
        for result in results:
            lead = parse_result(result, query, found_date)
            if lead is None:
                continue
            key = lead.linkedin_url.lower()
            if key in seen:
                continue
            seen.add(key)
            leads.append(lead)
            kept += 1
        logger.info("%-60s -> %d lead(s)", query[:60], kept)
        if client.budget_left <= 0:
            logger.warning("stopping early: search budget exhausted")
            break
    return leads


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.queries_file.is_file():
        logger.error("queries file not found: %s", args.queries_file)
        return 1

    all_queries = load_queries(args.queries_file.read_text(encoding="utf-8"))
    todays = slice_for_day(all_queries, args.slice_size)
    logger.info("%d total queries; running %d today", len(all_queries), len(todays))

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    engine_id = os.environ.get("GOOGLE_CX", "")

    if args.dry_run:
        # Still needs a key to actually query Google; if absent, just show the plan.
        if not (api_key and engine_id):
            logger.warning("no GOOGLE_API_KEY / GOOGLE_CX set; printing today's queries only")
            for q in todays:
                print(q)
            return 0

    if not (api_key and engine_id):
        logger.error("GOOGLE_API_KEY and GOOGLE_CX must be set")
        return 1

    client = GoogleSearchClient(api_key, engine_id, daily_budget=args.slice_size * args.pages)
    leads = collect_leads(todays, client, args.pages)
    logger.info("collected %d unique lead(s) from %d search call(s)", len(leads), client.calls_made)

    if args.dry_run:
        for lead in leads:
            print(" | ".join(lead.as_row()))
        return 0

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    sa_raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not (sheet_id and sa_raw):
        logger.error("GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON must be set")
        return 1

    writer = SheetWriter.from_service_account(load_service_account(sa_raw), sheet_id)
    added = writer.append_new(leads)
    logger.info("appended %d new lead(s) to the sheet", added)
    print(f"Done: {added} new lead(s) added; {len(leads)} found this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
