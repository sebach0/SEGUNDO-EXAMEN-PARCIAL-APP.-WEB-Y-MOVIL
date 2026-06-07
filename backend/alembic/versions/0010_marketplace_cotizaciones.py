"""Marketplace cotizaciones: distancia_km y servicios_ofrecidos."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0010_marketplace_cotizaciones"
down_revision: Union[str, None] = "0009_unificacion_operativa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0018_marketplace_cotizaciones.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("ALTER TABLE cotizaciones DROP COLUMN IF EXISTS servicios_ofrecidos;"))
    op.execute(text("ALTER TABLE cotizaciones DROP COLUMN IF EXISTS distancia_km;"))
