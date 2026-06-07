"""Fix permisos cotizaciones/servicios/kpis (codigo module:accion) + rol TALLER_RESPONSABLE."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0011_fix_cotizaciones_permisos"
down_revision: Union[str, None] = "0010_marketplace_cotizaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0019_fix_cotizaciones_permisos.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    pass
