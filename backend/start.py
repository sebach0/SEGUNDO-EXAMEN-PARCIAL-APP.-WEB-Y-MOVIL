#!/usr/bin/env python3
"""
Startup script for Render deployment.

- Connects to DB with retry (handles cold-start delays).
- Applies each SQL migration file individually, skipping ones already applied.
- Stamps Alembic at HEAD so subsequent deploys use alembic upgrade head.
- Execs uvicorn.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds


def get_sync_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    return url.replace("+asyncpg", "")


def connect_with_retry(conn_url: str) -> psycopg.Connection:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return psycopg.connect(conn_url, connect_timeout=15)
        except Exception as e:
            last_err = e
            print(f"DB connection attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Could not connect to DB after {MAX_RETRIES} attempts: {last_err}")


def alembic_at_head(conn_url: str) -> bool:
    """Returns True if alembic_version table exists with any revision (already set up)."""
    try:
        with connect_with_retry(conn_url) as conn:
            row = conn.execute(
                "SELECT version_num FROM alembic_version LIMIT 1"
            ).fetchone()
            return row is not None
    except Exception:
        return False


def apply_sql_files(conn_url: str) -> None:
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    # init.sql must run first
    init_sql = MIGRATIONS_DIR / "init.sql"
    if init_sql in sql_files:
        sql_files.remove(init_sql)
        sql_files.insert(0, init_sql)

    for f in sql_files:
        print(f"  -> {f.name} ...", end=" ", flush=True)
        try:
            # Each file gets its own connection+transaction so failures don't block the rest
            with psycopg.connect(conn_url, autocommit=True) as conn:
                conn.execute(f.read_text())
            print("OK")
        except Exception as e:
            # "already exists" errors are expected on re-runs — skip silently
            short = str(e).split("\n")[0]
            print(f"skipped ({short})")


def run(*args: str) -> None:
    print(f"$ {' '.join(args)}")
    subprocess.run(list(args), check=True)


def main() -> None:
    conn_url = get_sync_url()

    if alembic_at_head(conn_url):
        print("DB already initialised — running alembic upgrade head.")
        run("alembic", "upgrade", "head")
    else:
        print("Initialising database — applying SQL migration files.")
        apply_sql_files(conn_url)
        print("Stamping Alembic at HEAD.")
        run("alembic", "stamp", "head")

    print("Starting uvicorn...")
    os.execvp(
        "uvicorn",
        [
            "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", os.environ.get("UVICORN_PORT", "8000"),
        ],
    )


if __name__ == "__main__":
    main()
