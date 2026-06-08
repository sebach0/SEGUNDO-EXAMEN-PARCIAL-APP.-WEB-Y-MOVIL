#!/usr/bin/env python3
"""
Startup script for Render (fresh DB) and subsequent deploys.

Fresh DB  → apply all SQL migration files, then stamp Alembic at HEAD.
Existing  → run alembic upgrade head for any pending Python migrations.
Finally   → exec uvicorn.
"""
import os
import subprocess
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_sync_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    return url.replace("+asyncpg", "")


def schema_exists(conn_url: str) -> bool:
    with psycopg.connect(conn_url) as conn:
        row = conn.execute(
            "SELECT to_regclass('public.usuarios')"
        ).fetchone()
        return row is not None and row[0] is not None


def apply_all_sql(conn_url: str) -> None:
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    init_sql = MIGRATIONS_DIR / "init.sql"
    if init_sql in sql_files:
        sql_files.remove(init_sql)
        sql_files.insert(0, init_sql)

    with psycopg.connect(conn_url, autocommit=True) as conn:
        for f in sql_files:
            print(f"  -> {f.name}")
            conn.execute(f.read_text())
    print("All SQL files applied.")


def run(*args: str) -> None:
    print(f"$ {' '.join(args)}")
    subprocess.run(list(args), check=True)


def main() -> None:
    conn_url = get_sync_url()

    if schema_exists(conn_url):
        print("Schema exists — running pending Alembic migrations.")
        run("alembic", "upgrade", "head")
    else:
        print("Fresh database — applying all SQL files then stamping Alembic.")
        apply_all_sql(conn_url)
        run("alembic", "stamp", "head")

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
