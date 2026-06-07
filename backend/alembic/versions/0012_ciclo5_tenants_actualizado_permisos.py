"""Ciclo 5 Etapa 1A: tenants.actualizado_en + permiso tenants:asignar."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0012_ciclo5_tenants_et1a"
down_revision: Union[str, None] = "0011_fix_cotizaciones_permisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0020_ciclo5_tenants_actualizado_permisos.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("ALTER TABLE tenants DROP COLUMN IF EXISTS actualizado_en;"))
    op.execute(
        text(
            """
            DELETE FROM rol_permiso rp
            USING permisos p, roles r
            WHERE rp.permiso_id = p.id AND rp.rol_id = r.id
              AND r.nombre = 'ADMIN' AND p.codigo = 'tenants:asignar';
            DELETE FROM permisos WHERE codigo = 'tenants:asignar';
            """
        )
    )
