from datetime import date

from lead_crm.config import Company, is_excluded_client, titles_for_lane
from lead_crm.models import Contact, compute_next_touch
from lead_crm.output import dedupe, to_csv
from lead_crm.parse import parse_result
from lead_crm.queries import build_for_lane, build_query


# --- config / exclusion ---------------------------------------------------

def test_morocco_client_excluded_but_fixer_allowed():
    assert is_excluded_client("Morocco", is_morocco_fixer=False) is True
    assert is_excluded_client("Morocco", is_morocco_fixer=True) is False
    assert is_excluded_client("UK", is_morocco_fixer=False) is False


def test_titles_for_lane():
    assert "Head of Production" in titles_for_lane("1A")
    assert "Brand Manager" in titles_for_lane("2")
    assert "Photo Researcher" in titles_for_lane("3")


# --- query generation -----------------------------------------------------

def test_build_query_shape():
    c = Company("Raccoon London", "1A", "UK")
    dork = build_query(c, max_titles=2)
    assert dork.query.startswith("site:linkedin.com/in (")
    assert '"Raccoon London"' in dork.query
    assert " OR " in dork.query
    assert dork.lane == "1A"


def test_build_for_lane_filters_by_prefix():
    tier_a = build_for_lane("1A")
    assert all(d.lane == "1A" for d in tier_a)
    all_lane1 = build_for_lane("1")
    assert {d.lane for d in all_lane1} >= {"1A", "1B", "1C"}


# --- follow-up scheduling -------------------------------------------------

def test_next_touch_dates():
    base = date(2026, 7, 7)
    assert compute_next_touch("opened", base) == "2026-07-15"      # +8 days
    assert compute_next_touch("warm", base) == "2026-08-25"        # +7 weeks
    assert compute_next_touch("new", base) == ""                    # no touch


# --- parsing --------------------------------------------------------------

def test_parse_valid_profile():
    result = {
        "title": "Jane Producer - Senior Producer at Raccoon London",
        "link": "https://uk.linkedin.com/in/jane-producer-123",
        "snippet": "Senior Producer at Raccoon London.",
    }
    c = parse_result(result, "Raccoon London", "1A", "UK", today=date(2026, 7, 7))
    assert c is not None
    assert c.name == "Jane Producer"
    assert c.title == "Senior Producer"
    assert c.lane == "1A"
    assert c.status == "new"
    assert c.date_added == "2026-07-07"


def test_parse_rejects_company_mismatch():
    result = {
        "title": "Bob X - Producer at Some Other Co",
        "link": "https://www.linkedin.com/in/bobx/",
        "snippet": "Producer somewhere else.",
    }
    assert parse_result(result, "Raccoon London", "1A", "UK") is None


def test_parse_rejects_non_profile():
    result = {"title": "Jobs", "link": "https://www.linkedin.com/jobs/view/1", "snippet": ""}
    assert parse_result(result, "Raccoon London", "1A", "UK") is None


def test_parse_excludes_moroccan_client():
    result = {
        "title": "Sara - Producer at Casablanca Studio",
        "link": "https://ma.linkedin.com/in/sara/",
        "snippet": "Producer at Casablanca Studio",
    }
    # Moroccan, not a fixer -> excluded
    assert parse_result(result, "Casablanca Studio", "1A", "Morocco") is None
    # Moroccan fixer -> allowed
    assert parse_result(result, "Casablanca Studio", "1A", "Morocco", is_morocco_fixer=True) is not None


# --- output ---------------------------------------------------------------

def test_csv_has_header_and_rows():
    contacts = [Contact(name="A", title="Producer", company="X", lane="1A")]
    csv_text = to_csv(contacts)
    assert csv_text.splitlines()[0].startswith("name,title,company,lane,country")
    assert "Producer" in csv_text


def test_dedupe_by_linkedin_url():
    a = Contact(name="A", title="t", company="c", lane="1A", linkedin_url="https://linkedin.com/in/x")
    b = Contact(name="A dup", title="t", company="c", lane="1A", linkedin_url="https://linkedin.com/in/x")
    assert len(dedupe([a, b])) == 1
