"""Ciclo 2 fase 2: seguimiento solicitud, historial, taller/técnico, ETA (CU16–CU18).

DDL en SQL idempotente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0004_ciclo2_fase2_seguimiento"
down_revision: Union[str, None] = "0003_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "migrations" / "0003_ciclo2_fase2_seguimiento.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS solicitud_historial_estado CASCADE;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP CONSTRAINT IF EXISTS fk_solicitudes_taller;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP CONSTRAINT IF EXISTS fk_solicitudes_tecnico;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS taller_id;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS tecnico_id;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS tiempo_estimado_min;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS finalizada_at;"))
    op.execute(text("DROP TYPE IF EXISTS estado_solicitud_seguimiento CASCADE;"))
