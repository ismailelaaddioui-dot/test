"""Lane-based outreach CRM builder for commercial photography prospecting.

Unlike the sibling `lead_finder` package (built for mass editorial outreach),
this targets a precise, lane-prioritized pipeline: production companies and
agencies (Lane 1), brands (Lane 2), and a thin editorial lane (Lane 3). It
produces rows in a CRM tracker schema (lane, status, follow-up dates, …)
rather than a flat lead dump, and is designed to be run on-demand ~weekly.

Search execution itself is external (run the generated dorks, feed the
results back through `parse`), so nothing here depends on a paid search API.
"""

__version__ = "1.0.0"
