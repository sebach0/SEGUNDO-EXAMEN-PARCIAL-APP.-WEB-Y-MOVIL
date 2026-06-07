"""Ciclo 5 Etapa 1D-E: tenant_id cotizaciones/pagos + permisos."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0014_ciclo5_cotiz_pagos"
down_revision: Union[str, None] = "0013_ciclo5_reports_sla"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0022_ciclo5_cotizaciones_pagos_tenant.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS cotizacion_id;"))
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS tenant_id;"))
    op.execute(text("ALTER TABLE cotizacion_items DROP COLUMN IF EXISTS tenant_id;"))
    op.execute(text("ALTER TABLE cotizaciones DROP COLUMN IF EXISTS tenant_id;"))
    op.execute(
        text(
            """
            DELETE FROM rol_permiso rp USING permisos p, roles r
            WHERE rp.permiso_id = p.id AND rp.rol_id = r.id
              AND p.codigo IN ('cotizaciones:rechazar', 'pagos:admin');
            DELETE FROM permisos WHERE codigo IN ('cotizaciones:rechazar', 'pagos:admin');
            """
        )
    )
