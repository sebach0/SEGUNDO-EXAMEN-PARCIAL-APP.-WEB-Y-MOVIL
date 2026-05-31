# Valores TIMESTAMP sin time zone en PostgreSQL (init.sql): asyncpg no acepta tz-aware.
from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
