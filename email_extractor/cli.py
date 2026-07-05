"""Command-line interface for the email research/extraction tool."""

import argparse
import logging
import sys
from pathlib import Path

import requests

from .document_parser import SUPPORTED_EXTENSIONS
from .extractor import ExtractionPipeline
from .output_writer import write_emails_csv, write_emails_json, write_skip_log
from .web_crawler import DEFAULT_USER_AGENT, RateLimiter, RobotsCache

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find publicly listed contact email addresses from website URLs "
            "and/or local documents (PDF, DOCX, CSV, TXT)."
        )
    )
    parser.add_argument(
        "--urls-file", type=Path,
        help="CSV or TXT file listing website URLs, one per line.",
    )
    parser.add_argument(
        "--docs-dir", type=Path,
        help="Folder of local documents to parse (.pdf, .docx, .csv, .txt).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output"),
        help="Directory to write emails.csv, emails.json, skipped.csv (default: ./output).",
    )
    parser.add_argument(
        "--rate-limit", type=float, default=1.0,
        help="Minimum seconds between requests to the same domain (default: 1.0).",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0,
        help="Per-request timeout in seconds (default: 10.0).",
    )
    parser.add_argument(
        "--max-pages-per-site", type=int, default=8,
        help="Max pages fetched per site: homepage + contact/about/team pages (default: 8).",
    )
    parser.add_argument(
        "--user-agent", default=DEFAULT_USER_AGENT,
        help="User-Agent string sent with every HTTP request.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging.",
    )
    args = parser.parse_args(argv)

    if not args.urls_file and not args.docs_dir:
        parser.error("at least one of --urls-file or --docs-dir is required")

    return args


def _read_urls(path: Path) -> list[str]:
    urls = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def _iter_doc_files(docs_dir: Path):
    for path in sorted(docs_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def run(args: argparse.Namespace) -> ExtractionPipeline:
    pipeline = ExtractionPipeline()

    if args.docs_dir:
        if not args.docs_dir.is_dir():
            logger.error("--docs-dir %s is not a directory", args.docs_dir)
        else:
            for path in _iter_doc_files(args.docs_dir):
                pipeline.ingest_file(path)

    if args.urls_file:
        if not args.urls_file.is_file():
            logger.error("--urls-file %s does not exist", args.urls_file)
        else:
            urls = _read_urls(args.urls_file)
            session = requests.Session()
            session.headers["User-Agent"] = args.user_agent
            rate_limiter = RateLimiter(args.rate_limit)
            robots = RobotsCache(session, args.timeout, args.user_agent)
            for url in urls:
                try:
                    pipeline.ingest_site(
                        url, session, rate_limiter, robots,
                        args.timeout, args.max_pages_per_site,
                    )
                except Exception as exc:  # noqa: BLE001 - keep the run alive
                    pipeline.add_skip(url, f"unexpected error: {exc}")

    return pipeline


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    pipeline = run(args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = pipeline.records()
    skipped = pipeline.skipped()

    write_emails_csv(records, args.output_dir / "emails.csv")
    write_emails_json(records, args.output_dir / "emails.json")
    write_skip_log(skipped, args.output_dir / "skipped.csv")

    print(f"Found {len(records)} unique email(s); {len(skipped)} source(s) skipped.")
    print(f"Results written to {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
