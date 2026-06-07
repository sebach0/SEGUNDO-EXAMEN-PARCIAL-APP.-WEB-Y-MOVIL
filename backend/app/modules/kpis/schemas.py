from __future__ import annotations

from pydantic import BaseModel


class TallerEficiente(BaseModel):
    taller_id: int
    nombre_comercial: str
    tiempo_promedio_min: float
    total_atendidos: int


class ZonaIncidencia(BaseModel):
    zona: str
    total: int


class KpiSummaryRead(BaseModel):
    # Tiempos promedio (minutos)
    tiempo_promedio_asignacion_min: float | None
    tiempo_promedio_llegada_min: float | None
    tiempo_promedio_atencion_min: float | None

    # Conteos globales
    incidentes_activos: int
    incidentes_finalizados: int
    incidentes_cancelados: int

    # Cumplimiento SLA
    cumplimiento_sla_pct: float | None

    # Desglose
    incidentes_por_tipo: dict[str, int]
    zonas_con_mas_incidentes: list[ZonaIncidencia]
    talleres_mas_eficientes: list[TallerEficiente]
