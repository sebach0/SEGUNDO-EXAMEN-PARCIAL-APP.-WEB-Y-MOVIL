# KPIs operacionales desde solicitudes_emergencia (flujo real unificado).
from __future__ import annotations

from sqlalchemy import func, select, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ciclo4.incidentes.models import Zona
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.kpis.filters import (
    KpiFilters,
    apply_solicitud_filters,
    llegada_efectiva_col,
    tipo_incidente_col,
)
from app.modules.kpis.schemas import (
    AdminDashboardKpisRead,
    CancelledCaseRead,
    IncidentByTypeRead,
    KpiSummaryRead,
    SlaSummaryRead,
    TallerEficiente,
    ZonaIncidencia,
)
from app.modules.talleres_y_tecnicos.talleres.models import Taller

_ESTADOS_ACTIVOS = [
    EstadoSolicitudSeguimientoEnum.REGISTRADA,
    EstadoSolicitudSeguimientoEnum.EN_REVISION,
    EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
    EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
    EstadoSolicitudSeguimientoEnum.EN_CAMINO,
    EstadoSolicitudSeguimientoEnum.EN_ATENCION,
]


def _epoch_diff_minutes(col_end, col_start):
    return func.extract("epoch", col_end - col_start) / 60.0


def _round_min(value) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


async def get_counts(db: AsyncSession, filters: KpiFilters) -> tuple[int, int, int]:
    q = apply_solicitud_filters(
        select(
            func.count(case((SolicitudEmergencia.estado.in_(_ESTADOS_ACTIVOS), 1))).label("activos"),
            func.count(
                case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.FINALIZADA, 1))
            ).label("finalizados"),
            func.count(
                case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.CANCELADA, 1))
            ).label("cancelados"),
        ),
        filters,
    )
    row = (await db.execute(q)).one()
    return int(row.activos or 0), int(row.finalizados or 0), int(row.cancelados or 0)


async def get_average_assignment_minutes(db: AsyncSession, filters: KpiFilters) -> float | None:
    q = apply_solicitud_filters(
        select(
            func.avg(
                _epoch_diff_minutes(SolicitudEmergencia.asignado_en, SolicitudEmergencia.reportado_en)
            )
        ).where(
            SolicitudEmergencia.asignado_en.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
        ),
        filters,
    )
    return _round_min((await db.execute(q)).scalar())


async def get_average_arrival_minutes(db: AsyncSession, filters: KpiFilters) -> float | None:
    llegada = llegada_efectiva_col()
    q = apply_solicitud_filters(
        select(func.avg(_epoch_diff_minutes(llegada, SolicitudEmergencia.asignado_en))).where(
            llegada.isnot(None),
            SolicitudEmergencia.asignado_en.isnot(None),
        ),
        filters,
    )
    return _round_min((await db.execute(q)).scalar())


async def get_average_total_minutes(db: AsyncSession, filters: KpiFilters) -> float | None:
    q = apply_solicitud_filters(
        select(
            func.avg(
                _epoch_diff_minutes(SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en)
            )
        ).where(
            SolicitudEmergencia.finalizada_at.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
        ),
        filters,
    )
    return _round_min((await db.execute(q)).scalar())


async def get_sla_compliance_pct(db: AsyncSession, filters: KpiFilters) -> float | None:
    q = apply_solicitud_filters(
        select(
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
        ),
        filters,
    )
    row = (await db.execute(q)).one()
    if not row.total_fin or row.total_fin <= 0:
        return None
    return round(float(row.cumple) / float(row.total_fin) * 100, 1)


async def get_incidents_by_type(
    db: AsyncSession, filters: KpiFilters
) -> list[IncidentByTypeRead]:
    tipo_col = tipo_incidente_col()
    q = (
        apply_solicitud_filters(
            select(tipo_col.label("tipo"), func.count(SolicitudEmergencia.id).label("total")),
            filters,
        )
        .group_by(tipo_col)
        .order_by(func.count(SolicitudEmergencia.id).desc())
    )
    rows = (await db.execute(q)).all()
    return [IncidentByTypeRead(tipo=str(r.tipo), total=int(r.total)) for r in rows]


async def get_incidents_by_zone(db: AsyncSession, filters: KpiFilters) -> list[ZonaIncidencia]:
    q = (
        apply_solicitud_filters(
            select(Zona.nombre, func.count(SolicitudEmergencia.id).label("total")).join(
                Zona, SolicitudEmergencia.zona_id == Zona.id, isouter=True
            ),
            filters,
        )
        .group_by(Zona.nombre)
        .order_by(func.count(SolicitudEmergencia.id).desc())
        .limit(20)
    )
    rows = (await db.execute(q)).all()
    return [ZonaIncidencia(zona=(r.nombre or "Sin zona"), total=int(r.total)) for r in rows]


async def get_workshop_efficiency(
    db: AsyncSession, filters: KpiFilters, *, limit: int = 10
) -> list[TallerEficiente]:
    q = (
        apply_solicitud_filters(
            select(
                Taller.id.label("taller_id"),
                Taller.nombre_comercial,
                func.avg(
                    _epoch_diff_minutes(
                        SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en
                    )
                ).label("avg_min"),
                func.count(SolicitudEmergencia.id).label("total"),
            ).join(Taller, SolicitudEmergencia.taller_id == Taller.id),
            filters,
        )
        .where(SolicitudEmergencia.finalizada_at.isnot(None))
        .group_by(Taller.id, Taller.nombre_comercial)
        .order_by(text("avg_min ASC"))
        .limit(limit)
    )
    rows = (await db.execute(q)).all()
    return [
        TallerEficiente(
            taller_id=r.taller_id,
            nombre_comercial=r.nombre_comercial,
            tiempo_promedio_min=round(float(r.avg_min), 1),
            total_atendidos=int(r.total),
        )
        for r in rows
    ]


async def get_cancelled_cases(
    db: AsyncSession, filters: KpiFilters, *, limit: int = 100
) -> list[CancelledCaseRead]:
    q = (
        apply_solicitud_filters(
            select(
                SolicitudEmergencia.id,
                SolicitudEmergencia.cancelado_en,
                SolicitudEmergencia.motivo_cancelacion,
                SolicitudEmergencia.cancelacion_fase,
            ),
            filters,
        )
        .where(SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.CANCELADA)
        .order_by(SolicitudEmergencia.cancelado_en.desc().nullslast())
        .limit(limit)
    )
    rows = (await db.execute(q)).all()
    return [
        CancelledCaseRead(
            solicitud_id=r.id,
            cancelado_en=r.cancelado_en,
            motivo=r.motivo_cancelacion,
            fase=r.cancelacion_fase,
        )
        for r in rows
    ]


async def get_sla_summary(db: AsyncSession, filters: KpiFilters) -> SlaSummaryRead:
    activos, finalizados, cancelados = await get_counts(db, filters)
    q_total = apply_solicitud_filters(select(func.count(SolicitudEmergencia.id)), filters)
    total = int((await db.execute(q_total)).scalar() or 0)

    q_out = apply_solicitud_filters(
        select(func.count(SolicitudEmergencia.id)).where(
            SolicitudEmergencia.finalizada_at.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
            _epoch_diff_minutes(
                SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en
            )
            > SolicitudEmergencia.sla_minutos,
        ),
        filters,
    )
    fuera_sla = int((await db.execute(q_out)).scalar() or 0)

    return SlaSummaryRead(
        total_incidentes=total,
        incidentes_finalizados=finalizados,
        incidentes_cancelados=cancelados,
        cumplimiento_sla_pct=await get_sla_compliance_pct(db, filters),
        casos_fuera_sla=fuera_sla,
    )


async def get_admin_dashboard_kpis(db: AsyncSession, filters: KpiFilters) -> AdminDashboardKpisRead:
    activos, finalizados, cancelados = await get_counts(db, filters)
    q_total = apply_solicitud_filters(select(func.count(SolicitudEmergencia.id)), filters)
    total = int((await db.execute(q_total)).scalar() or 0)

    por_tipo = await get_incidents_by_type(db, filters)
    zonas = await get_incidents_by_zone(db, filters)
    talleres = await get_workshop_efficiency(db, filters)

    return AdminDashboardKpisRead(
        tenant_id=filters.tenant_id,
        total_incidents=total,
        average_assignment_minutes=await get_average_assignment_minutes(db, filters),
        average_arrival_minutes=await get_average_arrival_minutes(db, filters),
        average_total_minutes=await get_average_total_minutes(db, filters),
        active_incidents=activos,
        completed_incidents=finalizados,
        cancelled_cases=cancelados,
        sla_compliance_percentage=await get_sla_compliance_pct(db, filters),
        incidents_by_type=por_tipo,
        incidents_by_zone=zonas,
        top_workshops=talleres,
    )


async def get_kpi_summary(db: AsyncSession, *, tenant_id: int, **kwargs) -> KpiSummaryRead:
    """Compatibilidad Ciclo 4 — delega en funciones compartidas."""
    filters = KpiFilters(tenant_id=tenant_id, **kwargs)
    activos, finalizados, cancelados = await get_counts(db, filters)
    por_tipo_list = await get_incidents_by_type(db, filters)
    return KpiSummaryRead(
        tiempo_promedio_asignacion_min=await get_average_assignment_minutes(db, filters),
        tiempo_promedio_llegada_min=await get_average_arrival_minutes(db, filters),
        tiempo_promedio_atencion_min=await get_average_total_minutes(db, filters),
        incidentes_activos=activos,
        incidentes_finalizados=finalizados,
        incidentes_cancelados=cancelados,
        cumplimiento_sla_pct=await get_sla_compliance_pct(db, filters),
        incidentes_por_tipo={i.tipo: i.total for i in por_tipo_list},
        zonas_con_mas_incidentes=await get_incidents_by_zone(db, filters),
        talleres_mas_eficientes=await get_workshop_efficiency(db, filters),
    )
