# Filtros compartidos KPIs / reportes / SLA (Ciclo 5).
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import func

from app.modules.incidentes.emergencias.models import SolicitudEmergencia


@dataclass(frozen=True)
class KpiFilters:
    tenant_id: int
    desde: date | None = None
    hasta: date | None = None
    taller_id: int | None = None
    zona_id: int | None = None
    tipo_incidente_id: int | None = None
    tipo_incidente_nombre: str | None = None


def _dt_desde(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).replace(tzinfo=None)


def _dt_hasta_exclusive(d: date) -> datetime:
    return datetime(d.year, d.month, d.day + 1, tzinfo=timezone.utc).replace(tzinfo=None)


def tipo_incidente_col():
    """Columna derivada de clasificación IA en solicitudes_emergencia."""
    return func.coalesce(
        SolicitudEmergencia.ai_payload["clasificacion"]["categoria"].astext,
        "Sin tipo",
    )


def llegada_efectiva_col():
    """Llegada real o, si falta, timestamp en_atencion_en."""
    return func.coalesce(SolicitudEmergencia.llegada_real_en, SolicitudEmergencia.en_atencion_en)


def apply_solicitud_filters(query, filters: KpiFilters):
    q = query.where(
        (SolicitudEmergencia.tenant_id == filters.tenant_id)
        | (SolicitudEmergencia.tenant_id.is_(None))
    )
    if filters.taller_id is not None:
        q = q.where(SolicitudEmergencia.taller_id == filters.taller_id)
    if filters.zona_id is not None:
        q = q.where(SolicitudEmergencia.zona_id == filters.zona_id)
    if filters.desde is not None:
        q = q.where(SolicitudEmergencia.reportado_en >= _dt_desde(filters.desde))
    if filters.hasta is not None:
        q = q.where(SolicitudEmergencia.reportado_en < _dt_hasta_exclusive(filters.hasta))
    if filters.tipo_incidente_nombre is not None:
        q = q.where(
            func.lower(tipo_incidente_col()) == func.lower(filters.tipo_incidente_nombre)
        )
    return q
