"""Ciclo 4 Segunda Fase: servicios de taller, cotizaciones, cancelación legacy y pago con seguro."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0008_ciclo4_servicios_cot"
down_revision: Union[str, None] = "0007_ciclo4_tenants_incidentes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0016_ciclo4_servicios_cotizaciones.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS cotizacion_items CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS cotizaciones CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS estado_cotizacion CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS taller_servicios CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS servicios_catalogo CASCADE;"))
    op.execute(text("ALTER TABLE talleres DROP COLUMN IF EXISTS tiene_grua;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS motivo_cancelacion;"))
    op.execute(text("ALTER TABLE solicitudes_emergencia DROP COLUMN IF EXISTS cancelado_en;"))
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS responsable_pago;"))
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS monto_seguro;"))
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS numero_poliza;"))
    op.execute(text("ALTER TABLE pagos DROP COLUMN IF EXISTS aseguradora;"))
    op.execute(text("DROP TYPE IF EXISTS responsable_pago CASCADE;"))
