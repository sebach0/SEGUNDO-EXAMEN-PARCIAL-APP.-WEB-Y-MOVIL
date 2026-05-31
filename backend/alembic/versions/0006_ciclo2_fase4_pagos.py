"""Ciclo 2 fase 4: pagos de solicitud (CU20)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0006_ciclo2_fase4_pagos"
down_revision: Union[str, None] = "0005_ciclo2_fase3_comunicaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "migrations" / "0005_ciclo2_fase4_pagos.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS ux_pagos_un_pagado_por_solicitud;"))
    op.execute(text("DROP TABLE IF EXISTS pagos CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS metodo_pago CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS estado_pago CASCADE;"))
    # No eliminamos filas de permisos/rol_permiso (compartidos con otros entornos).
