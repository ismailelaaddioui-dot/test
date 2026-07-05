"""Data structures shared across the extraction pipeline."""

from dataclasses import dataclass, field


@dataclass
class Mention:
    """One place a given email address was found."""

    origin: str          # URL or file path
    context: str         # short snippet of surrounding text
    timestamp: str       # ISO-8601 UTC timestamp of when it was found


@dataclass
class EmailRecord:
    """A deduplicated email address plus every place it was seen."""

    email: str
    is_role_based: bool
    mentions: list[Mention] = field(default_factory=list)

    @property
    def first_seen(self) -> str:
        return min(m.timestamp for m in self.mentions)

    @property
    def last_seen(self) -> str:
        return max(m.timestamp for m in self.mentions)


@dataclass
class SkippedSource:
    """A source that was not processed, and why."""

    source: str
    reason: str
    timestamp: str
