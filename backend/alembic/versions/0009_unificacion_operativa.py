"""Unificación operativa: timestamps KPI, tenant, SLA y offline en solicitudes_emergencia."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0009_unificacion_operativa"
down_revision: Union[str, None] = "0008_ciclo4_servicios_cot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0017_unificacion_operativa.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS uq_solicitudes_tenant_client_uuid;"))
    op.execute(text("DROP INDEX IF EXISTS idx_solicitudes_zona_id;"))
    op.execute(text("DROP INDEX IF EXISTS idx_solicitudes_reportado_en;"))
    op.execute(text("DROP INDEX IF EXISTS idx_solicitudes_tenant_id;"))
    op.execute(text("DROP INDEX IF EXISTS idx_talleres_tenant_id;"))
    cols = (
        "zona_id", "sync_estado", "client_uuid", "retraso_notificado_en",
        "eta_origen", "eta_actualizado_en", "taller_habia_llegado",
        "cancelacion_fase", "cancelado_por_usuario_id", "sla_minutos",
        "llegada_real_en", "en_atencion_en", "en_camino_en", "asignado_en",
        "reportado_en", "tenant_id",
    )
    for col in cols:
        op.execute(text(f"ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS {col};"))
    op.execute(text("ALTER TABLE talleres DROP COLUMN IF EXISTS tenant_id;"))
