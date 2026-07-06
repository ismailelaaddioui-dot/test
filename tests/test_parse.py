from lead_finder.parse import is_profile_url, parse_result, query_anchor

DATE = "2026-07-06"


def test_query_anchor_takes_last_quoted_term():
    assert query_anchor('site:linkedin.com "photo editor" "Monocle"') == "Monocle"


def test_profile_url_accepts_in_paths():
    assert is_profile_url("https://uk.linkedin.com/in/sam-brogan-0b36a8100")
    assert is_profile_url("https://www.linkedin.com/in/erinaulov/")


def test_profile_url_rejects_jobs_posts_company():
    assert not is_profile_url("https://www.linkedin.com/jobs/view/creative-director-123")
    assert not is_profile_url("https://www.linkedin.com/posts/foster-partners_activity-6630")
    assert not is_profile_url("https://www.linkedin.com/company/monocle")


def test_parses_dash_separated_title():
    # Real shape from validation: "Name - Title - Company | LinkedIn"
    result = {
        "title": "Erin Aulov - Senior Visuals Editor - POLITICO | LinkedIn",
        "link": "https://www.linkedin.com/in/erinaulov/",
        "snippet": "Senior Visuals Editor at POLITICO ...",
    }
    lead = parse_result(result, 'site:linkedin.com "visuals editor" "POLITICO"', DATE)
    assert lead is not None
    assert lead.name == "Erin Aulov"
    assert lead.title == "Senior Visuals Editor"
    assert lead.company == "POLITICO"
    assert lead.linkedin_url == "https://www.linkedin.com/in/erinaulov/"


def test_parses_title_at_company():
    result = {
        "title": "Sam Brogan - Art Director at Monocle",
        "link": "https://uk.linkedin.com/in/sam-brogan-0b36a8100",
        "snippet": "Art Director at Monocle. London.",
    }
    lead = parse_result(result, 'site:linkedin.com "art director" "Monocle"', DATE)
    assert lead is not None
    assert lead.name == "Sam Brogan"
    assert lead.title == "Art Director"
    assert lead.company == "Monocle"
    assert lead.company_site == "monocle.com"  # resolved from the known-outlet map


def test_known_outlet_wins_as_company_and_resolves_domain():
    result = {
        "title": "Jane Doe - Photo Director - Condé Nast Traveller | LinkedIn",
        "link": "https://www.linkedin.com/in/janedoe/",
        "snippet": "Photo Director, Condé Nast Traveller",
    }
    lead = parse_result(result, 'site:linkedin.com "photo director" "Condé Nast Traveller"', DATE)
    assert lead.company == "Condé Nast Traveller"
    assert lead.company_site == "cntraveller.com"


def test_rejects_result_missing_the_anchor():
    # A film DoP surfacing on a magazine query: outlet not mentioned -> dropped.
    result = {
        "title": "Julian Sepulveda - Director of Photography - Mode of Motion | LinkedIn",
        "link": "https://www.linkedin.com/in/julian-sepulveda-2071281b4/",
        "snippet": "Cinematographer and videographer.",
    }
    lead = parse_result(result, 'site:linkedin.com "director of photography" "Monocle"', DATE)
    assert lead is None


def test_rejects_non_profile_link():
    result = {
        "title": "1000+ Editorial Creative Director jobs",
        "link": "https://www.linkedin.com/jobs/editorial-creative-director-jobs",
        "snippet": "",
    }
    assert parse_result(result, 'site:linkedin.com "creative director" "editorial"', DATE) is None


def test_strips_tracking_params_from_url():
    result = {
        "title": "Ann Lee - Picture Editor - Elle | LinkedIn",
        "link": "https://www.linkedin.com/in/annlee/?trk=public_profile",
        "snippet": "Picture Editor at Elle",
    }
    lead = parse_result(result, 'site:linkedin.com "picture editor" "Elle"', DATE)
    assert lead.linkedin_url == "https://www.linkedin.com/in/annlee/"
