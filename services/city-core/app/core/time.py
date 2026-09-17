"""UTC time helpers.

SQLite (used by the unit test suite) has no native timezone-aware datetime
type: a `DateTime(timezone=True)` column round-trips as a naive datetime,
while PostgreSQL preserves tzinfo. `ensure_aware` normalizes a value read
back from either backend before it is compared against `utcnow()`, so
expiry checks work the same way against both.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
