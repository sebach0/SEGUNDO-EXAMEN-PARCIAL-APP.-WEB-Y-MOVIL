# Alembic: motor síncrono psycopg; la app sigue con asyncpg.
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
import app.db_metadata  # noqa: F401, E402 — registra metadatos

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_sync_database_url() -> str:
    url = settings.DATABASE_URL
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg", 1)
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=get_sync_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_sync_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # PG IDENTITY (GENERATED …) vs cómo SQLAlchemy refleja “default” → evita migraciones fantasma
            compare_server_default=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
