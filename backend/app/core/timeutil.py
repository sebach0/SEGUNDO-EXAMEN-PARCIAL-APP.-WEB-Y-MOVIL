# Valores TIMESTAMP sin time zone en PostgreSQL (init.sql): asyncpg no acepta tz-aware.
from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime | None) -> datetime | None:
    """Convierte datetime aware/naive a UTC naive (compatible con TIMESTAMP WITHOUT TIME ZONE)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
