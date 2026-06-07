"""Ciclo 4: tenants, incidentes v2, tracking, eventos tiempo real, offline sync.

NO modifica solicitudes_emergencia (Ciclo 1-3 sigue funcionando).
Agrega tenant_id nullable a usuarios y lo actualiza al tenant por defecto.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0007_ciclo4_tenants_incidentes"
down_revision: Union[str, None] = "0006_ciclo2_fase4_pagos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "migrations"
    / "0015_ciclo4_tenants_incidentes.sql"
)


def upgrade() -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    op.execute(text(sql))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS errores_sincronizacion CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS sincronizacion_offline CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS eventos_tiempo_real CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS incidente_tracking CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS incidente_estado_historial CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS incidente_taller CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS incidentes CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS zonas CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS tipos_incidente CASCADE;"))
    op.execute(text("ALTER TABLE usuarios DROP COLUMN IF EXISTS tenant_id;"))
    op.execute(text("DROP TABLE IF EXISTS tenants CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS estado_incidente_v2 CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS sync_estado_incidente CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS origen_incidente CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS estado_incidente_taller CASCADE;"))
