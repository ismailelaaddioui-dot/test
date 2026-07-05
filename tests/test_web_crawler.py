from email_extractor.web_crawler import CANDIDATE_PATHS, RateLimiter, RobotsCache, crawl_site


class FakeResponse:
    def __init__(self, status_code=200, text="", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"Content-Type": "text/html"}


class FakeSession:
    """Serves canned responses keyed by exact URL, no real network calls."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.requested_urls = []

    def get(self, url, timeout=None):
        self.requested_urls.append(url)
        if url not in self.responses:
            return FakeResponse(status_code=404)
        return self.responses[url]


HOME_HTML = """
<html><head><title>Acme Home</title></head>
<body>
  <a href="/contact">Contact us</a>
  <a href="/careers">Careers</a>
  <p>General inquiries: hello@acme.com</p>
</body></html>
"""

CONTACT_HTML = """
<html><head><title>Contact Acme</title></head>
<body><a href="mailto:sales@acme.com">Email Sales</a></body></html>
"""


def _build(responses, allow_all_robots=True):
    session = FakeSession(responses)
    robots_text = "" if allow_all_robots else "User-agent: *\nDisallow: /"
    session.responses["https://acme.com/robots.txt"] = FakeResponse(text=robots_text)
    robots = RobotsCache(session, timeout=5, user_agent="TestBot")
    rate_limiter = RateLimiter(min_interval=0)
    return session, robots, rate_limiter


def test_crawl_site_fetches_home_and_discovered_contact_page():
    responses = {
        "https://acme.com/": FakeResponse(text=HOME_HTML),
        "https://acme.com/contact": FakeResponse(text=CONTACT_HTML),
    }
    session, robots, rate_limiter = _build(responses)

    result = crawl_site(
        "https://acme.com", session, rate_limiter, robots, timeout=5, max_pages=10
    )

    fetched_urls = {url for url, _, _ in result.pages}
    assert "https://acme.com/" in fetched_urls
    assert "https://acme.com/contact" in fetched_urls


def test_crawl_site_respects_robots_disallow():
    responses = {"https://acme.com/": FakeResponse(text=HOME_HTML)}
    session, robots, rate_limiter = _build(responses, allow_all_robots=False)

    result = crawl_site(
        "https://acme.com", session, rate_limiter, robots, timeout=5, max_pages=10
    )

    assert result.pages == []
    assert any("robots.txt" in reason for _, reason in result.skipped)


def test_crawl_site_logs_404_as_skip():
    responses = {"https://acme.com/": FakeResponse(text=HOME_HTML)}
    session, robots, rate_limiter = _build(responses)

    result = crawl_site(
        "https://acme.com", session, rate_limiter, robots, timeout=5, max_pages=len(CANDIDATE_PATHS)
    )

    skipped_urls = {url for url, _ in result.skipped}
    assert "https://acme.com/about" in skipped_urls


def test_crawl_site_stops_at_max_pages():
    responses = {"https://acme.com/": FakeResponse(text=HOME_HTML)}
    session, robots, rate_limiter = _build(responses)

    result = crawl_site(
        "https://acme.com", session, rate_limiter, robots, timeout=5, max_pages=1
    )

    assert len(session.requested_urls) <= 1 + 1  # +1 for robots.txt fetch
