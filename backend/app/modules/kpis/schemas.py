from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TallerEficiente(BaseModel):
    taller_id: int
    nombre_comercial: str
    tiempo_promedio_min: float
    total_atendidos: int


class ZonaIncidencia(BaseModel):
    zona: str
    total: int


class IncidentByTypeRead(BaseModel):
    tipo: str
    total: int


class CancelledCaseRead(BaseModel):
    solicitud_id: int
    cancelado_en: datetime | None = None
    motivo: str | None = None
    fase: str | None = None


class SlaSummaryRead(BaseModel):
    total_incidentes: int
    incidentes_finalizados: int
    incidentes_cancelados: int
    cumplimiento_sla_pct: float | None
    casos_fuera_sla: int


class AdminDashboardKpisRead(BaseModel):
    tenant_id: int
    total_incidents: int
    average_assignment_minutes: float | None
    average_arrival_minutes: float | None
    average_total_minutes: float | None
    active_incidents: int
    completed_incidents: int
    cancelled_cases: int
    sla_compliance_percentage: float | None
    incidents_by_type: list[IncidentByTypeRead]
    incidents_by_zone: list[ZonaIncidencia]
    top_workshops: list[TallerEficiente]


class KpiSummaryRead(BaseModel):
    tiempo_promedio_asignacion_min: float | None
    tiempo_promedio_llegada_min: float | None
    tiempo_promedio_atencion_min: float | None
    incidentes_activos: int
    incidentes_finalizados: int
    incidentes_cancelados: int
    cumplimiento_sla_pct: float | None
    incidentes_por_tipo: dict[str, int]
    zonas_con_mas_incidentes: list[ZonaIncidencia]
    talleres_mas_eficientes: list[TallerEficiente]
