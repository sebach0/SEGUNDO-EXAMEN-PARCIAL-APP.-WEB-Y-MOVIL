"""Ciclo 2 fase 3: notificaciones, mensajes solicitud, tokens FCM (CU19, CU21)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0005_ciclo2_fase3_comunicaciones"
down_revision: Union[str, None] = "0004_ciclo2_fase2_seguimiento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "migrations" / "0004_ciclo2_fase3_comunicaciones.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS usuario_fcm_tokens CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS solicitud_mensajes CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS notificaciones CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS tipo_notificacion CASCADE;"))
