# Photo-desk Lead Finder

Builds a daily, deduplicated list of magazine / agency **photo editors, picture
editors, art directors** (and similar hiring roles) by running
`site:linkedin.com "<role>" "<outlet>"` Google searches, and appends new people
to a **Google Sheet**. You then look each person up in snov.io (or similar),
get their email, and send your pitch by hand.

It runs itself once a day on **GitHub Actions**, entirely on **free tiers**.

```
queries.txt ──▶ GitHub Actions (daily cron)
                     │
                     ├─ Google Custom Search API   (find LinkedIn profiles)
                     ├─ parse Name / Title / Company / Company-site / URL
                     ├─ drop noise (jobs, posts, off-topic hits)
                     ├─ dedupe against the Sheet
                     └─▶ append new rows to your Google Sheet
```

Output columns: `name | title | company | company_site | linkedin_url | query | found_date`

---

## How it works

- **`queries.txt`** holds the dork queries (873 role×outlet combos out of the
  box). Edit it directly, or edit the lists in **`generate_queries.py`** and run
  `python generate_queries.py` to regenerate it.
- The free search API allows ~100 queries/day, and the list is bigger than that,
  so each day the tool runs a **rotating slice** (default 90). Over ~10 days it
  cycles through the whole list, then repeats to catch newly-listed people. **Your
  Sheet grows every day** — you never wait for a full cycle.
- Results are filtered to real profiles only (`linkedin.com/in/…`), and a result
  is kept only if the query's outlet actually appears in it — that removes
  cross-topic noise like film/TV "director of photography" hits.
- Dedup is by LinkedIn URL against what's already in the Sheet, so nobody is
  added twice.

## Add more queries anytime

Append lines to `queries.txt` (format: `site:linkedin.com "<role>" "<outlet>"`),
or add outlets/roles in `generate_queries.py` and rerun it. The daily job picks
up the larger list automatically on its next run.

---

## One-time setup (all free, ~15 min)

You need four secrets. Steps 1–2 are Google Search; step 3 is Google Sheets
access; step 4 puts them into GitHub.

### 1. Google Custom Search API key
1. Go to <https://console.cloud.google.com/> and create a project (or reuse one).
2. Enable **Custom Search API**:
   <https://console.cloud.google.com/apis/library/customsearch.googleapis.com>
3. Create an API key under **APIs & Services → Credentials → Create credentials →
   API key**. Copy it → this is **`GOOGLE_API_KEY`**.

### 2. Programmable Search Engine ID
1. Go to <https://programmablesearchengine.google.com/controlpanel/create>.
2. Choose **Search the entire web**, create the engine.
3. Open its **Control Panel → Basics** and copy the **Search engine ID** →
   this is **`GOOGLE_CX`**.

### 3. Google service account + share the Sheet
1. Create the Sheet you want results in. Its URL looks like
   `https://docs.google.com/spreadsheets/d/`**`THIS_IS_THE_ID`**`/edit`.
   Copy that ID → **`GOOGLE_SHEET_ID`**.
2. In Google Cloud → **APIs & Services → Enable APIs** → enable **Google Sheets API**.
3. **IAM & Admin → Service Accounts → Create service account.** After creating it,
   open it → **Keys → Add key → Create new key → JSON**. A JSON file downloads.
4. Open that JSON, copy its **entire contents** → this is
   **`GOOGLE_SERVICE_ACCOUNT_JSON`**.
5. In the JSON find `"client_email"` (looks like
   `something@project.iam.gserviceaccount.com`). **Share your Sheet** with that
   email as **Editor** (the same way you'd share with a person).

### 4. Add the secrets to GitHub
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**, and add all four:

| Secret name | Value |
| --- | --- |
| `GOOGLE_API_KEY` | from step 1 |
| `GOOGLE_CX` | from step 2 |
| `GOOGLE_SHEET_ID` | from step 3.1 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | full JSON from step 3.4 |

That's it. The workflow in `.github/workflows/daily.yml` runs every day at
07:00 UTC. To test immediately, go to the **Actions** tab → **Daily lead finder**
→ **Run workflow**.

---

## Run it locally (optional)

```bash
pip install -r requirements.txt

# Just show which queries today's slice would run (no keys needed):
python -m lead_finder --dry-run --slice-size 5

# Actually search and print leads (needs the two search secrets as env vars):
GOOGLE_API_KEY=... GOOGLE_CX=... python -m lead_finder --dry-run --slice-size 5

# Full run writing to the Sheet (needs all four):
GOOGLE_API_KEY=... GOOGLE_CX=... GOOGLE_SHEET_ID=... \
GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service_account.json)" \
python -m lead_finder --slice-size 90
```

### CLI flags
| Flag | Default | Meaning |
| --- | --- | --- |
| `--queries-file` | `queries.txt` | the dork list |
| `--slice-size` | `90` | queries to run this invocation (keep ≤ 100 for free tier) |
| `--pages` | `1` | result pages per query (10 results each) |
| `--dry-run` | off | print instead of writing to Sheets |
| `-v/--verbose` | off | debug logging |

## Tests

```bash
python -m pytest
```

---

## Notes & limits

- **Free-tier budget:** 100 searches/day. `--slice-size 90` leaves headroom.
  Bigger query lists just take more days per full cycle — that's fine.
- **LinkedIn coverage:** the tool reads Google's public index, the same results
  you'd get typing the dork into a browser. Google indexes only some LinkedIn
  content, so yield per query is often a handful of people — volume comes from
  the breadth of the query list.
- **Company site** is filled from a built-in map of known outlets
  (`lead_finder/domains.py`); city-based results may have a blank domain you can
  fill in by hand. Add outlets to that map anytime.
- **Compliance:** this only collects public search results into a sheet (the
  automated equivalent of your own Googling) and leaves the actual email-finding
  to a dedicated tool. It does **not** scrape LinkedIn pages. Keep outreach
  compliant with GDPR/CAN-SPAM.
