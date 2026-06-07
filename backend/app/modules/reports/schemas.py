from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class IncidentReportRow(BaseModel):
    solicitud_id: int
    cliente: str | None = None
    vehiculo_placa: str | None = None
    tipo_incidente: str | None = None
    zona: str | None = None
    taller: str | None = None
    estado: str
    reportado_en: datetime | None = None
    asignado_en: datetime | None = None
    en_atencion_en: datetime | None = None
    finalizado_en: datetime | None = None
    minutos_asignacion: float | None = None
    minutos_llegada: float | None = None
    cumple_sla: bool | None = None
    monto_pagado: Decimal | None = None


class ReportTotals(BaseModel):
    total: int
    finalizados: int = 0
    cancelados: int = 0
    cumplimiento_sla_pct: float | None = None


class IncidentReportRead(BaseModel):
    items: list[IncidentReportRow]
    totals: ReportTotals
    message: str | None = None


class PerformanceReportRead(BaseModel):
    promedio_asignacion_min: float | None
    promedio_llegada_min: float | None
    promedio_total_min: float | None
    cumplimiento_sla_pct: float | None
    total_incidentes: int
    message: str | None = None


class WorkshopReportRow(BaseModel):
    taller_id: int
    nombre_comercial: str
    total_servicios: int
    finalizados: int
    cancelados: int
    promedio_asignacion_min: float | None
    promedio_llegada_min: float | None
    cumplimiento_sla_pct: float | None


class WorkshopReportRead(BaseModel):
    items: list[WorkshopReportRow]
    totals: ReportTotals
    message: str | None = None


class CancellationReportRead(BaseModel):
    items: list[IncidentReportRow]
    totals: ReportTotals
    message: str | None = None
