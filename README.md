# Email Research & Extraction Tool

Finds publicly listed contact email addresses from website URLs and/or local
documents (PDF, DOCX, CSV, TXT), and writes a clean, deduplicated dataset to
CSV and JSON.

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Usage

```bash
# From a list of website URLs (one per line, CSV or TXT)
python3 -m email_extractor --urls-file urls.txt --output-dir output

# From a folder of local documents
python3 -m email_extractor --docs-dir ./documents --output-dir output

# Both at once, with tuning flags
python3 -m email_extractor \
  --urls-file urls.txt \
  --docs-dir ./documents \
  --output-dir output \
  --rate-limit 1.0 \
  --max-pages-per-site 8 \
  --timeout 10 \
  --user-agent "MyCompanyResearchBot/1.0 (+contact: you@company.com)" \
  --verbose
```

### CLI arguments

| Flag | Default | Description |
|---|---|---|
| `--urls-file` | – | CSV/TXT file of website URLs, one per line |
| `--docs-dir` | – | Folder of `.pdf`, `.docx`, `.csv`, `.txt` files to parse |
| `--output-dir` | `output` | Where `emails.csv`, `emails.json`, `skipped.csv` are written |
| `--rate-limit` | `1.0` | Minimum seconds between requests to the same domain |
| `--timeout` | `10.0` | Per-request timeout (seconds) |
| `--max-pages-per-site` | `8` | Cap on pages fetched per site |
| `--user-agent` | descriptive default | User-Agent string sent with every request |
| `-v/--verbose` | off | Debug logging |

At least one of `--urls-file` / `--docs-dir` is required.

## Output

- **`emails.csv` / `emails.json`** — one row/object per unique email address:
  `email`, `is_role_based` (info@/sales@/support@-style vs. personal),
  the source(s) it was found on, a short context snippet, and first/last-seen
  timestamps.
- **`skipped.csv`** — every source that was skipped (robots.txt disallow,
  404, timeout, unparseable file, etc.) with a reason and timestamp.

## How extraction works

- **Plain addresses** are matched with a standard email regex.
- **Obfuscated addresses** such as `name [at] domain [dot] com` or
  `name at domain dot com` are also detected and reconstructed.
- Common false positives are filtered out: placeholder domains
  (`example.com`, `test.com`, ...) and asset-filename look-alikes like
  `photo@2x.png`.
- Addresses are deduplicated case-insensitively; a record keeps every
  page/file it was seen on.

## Compliance notes

This tool is built to stay within normal, polite web-scraping practice for
**publicly listed contact information**:

- **robots.txt is always checked** before fetching any page, using
  `urllib.robotparser`. Disallowed pages are skipped and logged, never
  fetched.
- **Rate limiting**: by default no more than 1 request/second per domain
  (configurable via `--rate-limit`).
- **Narrow scope, not a crawler**: only the homepage and a small, fixed set
  of likely public contact pages (`/contact`, `/about`, `/team`, and
  variants, plus same-domain links whose URL/text mentions
  contact/about/team) are fetched — capped by `--max-pages-per-site`. There
  is no recursive/deep crawling of a site.
- **Descriptive User-Agent**: the default identifies the tool and its
  purpose; set `--user-agent` to include your own contact details.
- You are responsible for reviewing each target site's Terms of Service
  before crawling it — this tool does not attempt to detect or interpret
  ToS text, it only enforces robots.txt and rate limits mechanically.
- Only use this against sites/documents you have the right to collect
  contact data from, and handle the resulting personal data (where any
  individual, non-role addresses are collected) in line with applicable
  privacy law (e.g. GDPR/CAN-SPAM) for your use case.

## Project layout

```
email_extractor/
  cli.py              CLI argument parsing and orchestration
  extractor.py         Pipeline: text -> deduplicated EmailRecords
  email_patterns.py    Regex extraction, de-obfuscation, validation
  web_crawler.py        robots.txt, rate limiting, contact-page discovery
  document_parser.py    PDF/DOCX/CSV/TXT text extraction
  output_writer.py      CSV/JSON/skip-log writers
  models.py             EmailRecord / Mention / SkippedSource dataclasses
tests/                  pytest unit tests (no live network calls)
```

## Running tests

```bash
python3 -m pytest
```
