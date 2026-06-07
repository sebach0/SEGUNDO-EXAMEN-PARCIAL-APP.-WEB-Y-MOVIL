from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WorkshopSlaRead(BaseModel):
    workshop_id: int
    workshop_name: str
    total_cases: int
    completed_cases: int
    cancelled_cases: int
    average_assignment_minutes: float | None
    average_arrival_minutes: float | None
    sla_compliance_percentage: float | None
    cases_out_of_sla: int


class SlaCaseDetailRead(BaseModel):
    solicitud_id: int
    reportado_en: datetime | None
    finalizado_en: datetime | None
    sla_minutos: int
    minutos_totales: float | None
    cumple_sla: bool


class WorkshopSlaDetailRead(BaseModel):
    workshop: WorkshopSlaRead
    cases_out_of_sla: list[SlaCaseDetailRead]
