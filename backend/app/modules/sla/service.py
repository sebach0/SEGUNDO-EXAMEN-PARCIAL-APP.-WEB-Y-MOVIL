# Cumplimiento SLA por taller (CU50).
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.kpis.filters import KpiFilters, apply_solicitud_filters, llegada_efectiva_col
from app.modules.sla.schemas import SlaCaseDetailRead, WorkshopSlaDetailRead, WorkshopSlaRead
from app.modules.talleres_y_tecnicos.talleres.models import Taller


def _epoch_diff_minutes(col_end, col_start):
    return func.extract("epoch", col_end - col_start) / 60.0


async def _workshop_sla_row(db: AsyncSession, filters: KpiFilters, taller_id: int) -> WorkshopSlaRead | None:
    llegada = llegada_efectiva_col()
    f = KpiFilters(
        tenant_id=filters.tenant_id,
        desde=filters.desde,
        hasta=filters.hasta,
        taller_id=taller_id,
        zona_id=filters.zona_id,
        tipo_incidente_id=filters.tipo_incidente_id,
        tipo_incidente_nombre=filters.tipo_incidente_nombre,
    )
    q = apply_solicitud_filters(
        select(
            Taller.id,
            Taller.nombre_comercial,
            func.count(SolicitudEmergencia.id).label("total"),
            func.count(
                case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.FINALIZADA, 1))
            ).label("completed"),
            func.count(
                case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.CANCELADA, 1))
            ).label("cancelled"),
            func.avg(
                _epoch_diff_minutes(SolicitudEmergencia.asignado_en, SolicitudEmergencia.reportado_en)
            ).label("avg_asig"),
            func.avg(_epoch_diff_minutes(llegada, SolicitudEmergencia.asignado_en)).label("avg_llegada"),
            func.count(
                case(
                    (
                        (
                            SolicitudEmergencia.finalizada_at.isnot(None)
                            & SolicitudEmergencia.reportado_en.isnot(None)
                            & (
                                _epoch_diff_minutes(
                                    SolicitudEmergencia.finalizada_at,
                                    SolicitudEmergencia.reportado_en,
                                )
                                <= SolicitudEmergencia.sla_minutos
                            )
                        ),
                        1,
                    )
                )
            ).label("cumple"),
            func.count(case((SolicitudEmergencia.finalizada_at.isnot(None), 1))).label("total_fin"),
            func.count(
                case(
                    (
                        (
                            SolicitudEmergencia.finalizada_at.isnot(None)
                            & SolicitudEmergencia.reportado_en.isnot(None)
                            & (
                                _epoch_diff_minutes(
                                    SolicitudEmergencia.finalizada_at,
                                    SolicitudEmergencia.reportado_en,
                                )
                                > SolicitudEmergencia.sla_minutos
                            )
                        ),
                        1,
                    )
                )
            ).label("fuera_sla"),
        )
        .join(Taller, SolicitudEmergencia.taller_id == Taller.id)
        .where(Taller.id == taller_id),
        f,
    ).group_by(Taller.id, Taller.nombre_comercial)

    row = (await db.execute(q)).one_or_none()
    if row is None or row.total == 0:
        return None

    sla_pct: float | None = None
    if row.total_fin and row.total_fin > 0:
        sla_pct = round(float(row.cumple or 0) / float(row.total_fin) * 100, 1)

    return WorkshopSlaRead(
        workshop_id=row.id,
        workshop_name=row.nombre_comercial,
        total_cases=int(row.total),
        completed_cases=int(row.completed or 0),
        cancelled_cases=int(row.cancelled or 0),
        average_assignment_minutes=round(float(row.avg_asig), 1) if row.avg_asig else None,
        average_arrival_minutes=round(float(row.avg_llegada), 1) if row.avg_llegada else None,
        sla_compliance_percentage=sla_pct,
        cases_out_of_sla=int(row.fuera_sla or 0),
    )


async def list_workshops_sla(db: AsyncSession, filters: KpiFilters) -> list[WorkshopSlaRead]:
    q_ids = apply_solicitud_filters(
        select(Taller.id.distinct()).join(
            SolicitudEmergencia, SolicitudEmergencia.taller_id == Taller.id
        ),
        filters,
    )
    taller_ids = [row[0] for row in (await db.execute(q_ids)).all()]
    result: list[WorkshopSlaRead] = []
    for tid in taller_ids:
        row = await _workshop_sla_row(db, filters, tid)
        if row is not None:
            result.append(row)
    result.sort(key=lambda x: x.sla_compliance_percentage or 0, reverse=True)
    return result


async def get_workshop_sla_detail(
    db: AsyncSession,
    filters: KpiFilters,
    workshop_id: int,
) -> WorkshopSlaDetailRead:
    summary = await _workshop_sla_row(db, filters, workshop_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Taller sin casos en el periodo indicado")

    f = KpiFilters(
        tenant_id=filters.tenant_id,
        desde=filters.desde,
        hasta=filters.hasta,
        taller_id=workshop_id,
        zona_id=filters.zona_id,
        tipo_incidente_id=filters.tipo_incidente_id,
        tipo_incidente_nombre=filters.tipo_incidente_nombre,
    )
    q = apply_solicitud_filters(
        select(
            SolicitudEmergencia.id,
            SolicitudEmergencia.reportado_en,
            SolicitudEmergencia.finalizada_at,
            SolicitudEmergencia.sla_minutos,
        ).where(
            SolicitudEmergencia.finalizada_at.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
            _epoch_diff_minutes(
                SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en
            )
            > SolicitudEmergencia.sla_minutos,
        ),
        f,
    ).order_by(SolicitudEmergencia.finalizada_at.desc())

    rows = (await db.execute(q)).all()
    cases: list[SlaCaseDetailRead] = []
    for r in rows:
        minutos = (r.finalizada_at - r.reportado_en).total_seconds() / 60.0
        cases.append(
            SlaCaseDetailRead(
                solicitud_id=r.id,
                reportado_en=r.reportado_en,
                finalizado_en=r.finalizada_at,
                sla_minutos=r.sla_minutos,
                minutos_totales=round(minutos, 1),
                cumple_sla=False,
            )
        )

    return WorkshopSlaDetailRead(workshop=summary, cases_out_of_sla=cases)
