"""Daily LinkedIn lead-list builder for photographer outreach.

Runs Google `site:linkedin.com "<role>" "<outlet>"` dork queries through the
Google Custom Search API, parses each result into Name / Title / Company /
Company-site / LinkedIn URL, deduplicates, and appends new people to a Google
Sheet. Designed to run once a day on GitHub Actions, free tier.
"""

__version__ = "1.0.0"
