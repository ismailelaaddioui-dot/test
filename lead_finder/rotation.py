"""Pick which slice of the query list to run today.

The free Google Custom Search tier allows ~100 queries/day, but the full
dork list is much larger. Rather than keep state in a file, we derive the
day's slice deterministically from the date: each day advances by one slice,
wrapping around, so over `ceil(total / slice_size)` days every query runs,
then the cycle repeats and re-checks for newly-indexed people.
"""

from datetime import date


def load_queries(text: str) -> list[str]:
    """Parse a queries file: one per line, blanks and '#' comments ignored."""
    queries = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            queries.append(stripped)
    return queries


def slice_for_day(
    queries: list[str],
    slice_size: int,
    day: date | None = None,
) -> list[str]:
    """Return today's contiguous (wrapping) slice of `slice_size` queries."""
    if not queries:
        return []
    slice_size = max(1, min(slice_size, len(queries)))
    day = day or date.today()

    # Number of distinct slices needed to cover the whole list.
    num_slices = (len(queries) + slice_size - 1) // slice_size
    # Advance one slice per day, wrapping across the cycle.
    slice_index = day.toordinal() % num_slices
    start = slice_index * slice_size
    return queries[start:start + slice_size]
