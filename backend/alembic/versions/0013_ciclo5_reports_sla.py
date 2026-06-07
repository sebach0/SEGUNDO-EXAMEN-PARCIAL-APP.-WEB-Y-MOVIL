"""Ciclo 5 Etapa 1B: permisos reports + sla."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0013_ciclo5_reports_sla"
down_revision: Union[str, None] = "0012_ciclo5_tenants_et1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0021_ciclo5_reports_sla_permisos.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(
        text(
            """
            DELETE FROM rol_permiso rp
            USING permisos p, roles r
            WHERE rp.permiso_id = p.id AND rp.rol_id = r.id
              AND r.nombre = 'ADMIN'
              AND p.codigo IN ('reports:leer', 'reports:exportar', 'sla:leer');
            DELETE FROM permisos WHERE codigo IN ('reports:leer', 'reports:exportar', 'sla:leer');
            """
        )
    )
