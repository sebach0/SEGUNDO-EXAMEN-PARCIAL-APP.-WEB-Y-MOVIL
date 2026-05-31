"""Ciclo 2 fase 1: solicitudes de emergencia, ubicaciones, evidencias (CU11–CU15).

DDL en archivo SQL idempotente. Tras aplicar: `alembic stamp 0002_ciclo2_fase1_emergencias`
si ejecutaste el SQL a mano sin pasar por upgrade.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0002_ciclo2_fase1_emergencias"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "migrations" / "0002_ciclo2_fase1_emergencias.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS solicitud_evidencias CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS solicitud_ubicaciones CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS solicitudes_emergencia CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS tipo_evidencia_solicitud CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS estado_solicitud_emergencia CASCADE;"))
