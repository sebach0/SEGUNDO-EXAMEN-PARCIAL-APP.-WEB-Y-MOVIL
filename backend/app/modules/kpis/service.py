# KPIs operacionales desde solicitudes_emergencia (flujo real unificado).
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ciclo4.incidentes.models import Zona
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.kpis.schemas import KpiSummaryRead, TallerEficiente, ZonaIncidencia
from app.modules.talleres_y_tecnicos.talleres.models import Taller


def _epoch_diff_minutes(col_end, col_start):
    return func.extract("epoch", col_end - col_start) / 60.0


async def get_kpi_summary(
    db: AsyncSession,
    *,
    tenant_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    taller_id: int | None = None,
) -> KpiSummaryRead:
    def base_filter(q):
        q = q.where(
            (SolicitudEmergencia.tenant_id == tenant_id)
            | (SolicitudEmergencia.tenant_id.is_(None))
        )
        if taller_id is not None:
            q = q.where(SolicitudEmergencia.taller_id == taller_id)
        if desde:
            q = q.where(
                SolicitudEmergencia.reportado_en
                >= datetime(desde.year, desde.month, desde.day, tzinfo=timezone.utc).replace(tzinfo=None)
            )
        if hasta:
            q = q.where(
                SolicitudEmergencia.reportado_en
                < datetime(hasta.year, hasta.month, hasta.day + 1, tzinfo=timezone.utc).replace(tzinfo=None)
            )
        return q

    estados_activos = [
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
        EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.EN_CAMINO,
        EstadoSolicitudSeguimientoEnum.EN_ATENCION,
    ]

    q_counts = base_filter(
        select(
            func.count(case((SolicitudEmergencia.estado.in_(estados_activos), 1))).label("activos"),
            func.count(case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.FINALIZADA, 1))).label(
                "finalizados"
            ),
            func.count(case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.CANCELADA, 1))).label(
                "cancelados"
            ),
        )
    )
    row_counts = (await db.execute(q_counts)).one()
    activos = int(row_counts.activos or 0)
    finalizados = int(row_counts.finalizados or 0)
    cancelados = int(row_counts.cancelados or 0)

    q_asig = base_filter(
        select(func.avg(_epoch_diff_minutes(SolicitudEmergencia.asignado_en, SolicitudEmergencia.reportado_en))).where(
            SolicitudEmergencia.asignado_en.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
        )
    )
    tiempo_asig = (await db.execute(q_asig)).scalar()

    q_llegada = base_filter(
        select(
            func.avg(_epoch_diff_minutes(SolicitudEmergencia.llegada_real_en, SolicitudEmergencia.asignado_en))
        ).where(
            SolicitudEmergencia.llegada_real_en.isnot(None),
            SolicitudEmergencia.asignado_en.isnot(None),
        )
    )
    tiempo_llegada = (await db.execute(q_llegada)).scalar()

    q_total = base_filter(
        select(func.avg(_epoch_diff_minutes(SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en))).where(
            SolicitudEmergencia.finalizada_at.isnot(None),
            SolicitudEmergencia.reportado_en.isnot(None),
        )
    )
    tiempo_total = (await db.execute(q_total)).scalar()

    q_sla = base_filter(
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
        )
    )
    row_sla = (await db.execute(q_sla)).one()
    sla_pct: float | None = None
    if row_sla.total_fin and row_sla.total_fin > 0:
        sla_pct = round(float(row_sla.cumple) / float(row_sla.total_fin) * 100, 1)

    tipo_col = func.coalesce(
        SolicitudEmergencia.ai_payload["clasificacion"]["categoria"].astext,
        "Sin tipo",
    )
    q_tipo = base_filter(
        select(
            tipo_col.label("tipo"),
            func.count(SolicitudEmergencia.id).label("total"),
        )
    ).group_by(tipo_col).order_by(func.count(SolicitudEmergencia.id).desc())
    rows_tipo = (await db.execute(q_tipo)).all()
    por_tipo = {str(r.tipo): int(r.total) for r in rows_tipo}

    q_zona = (
        base_filter(
            select(Zona.nombre, func.count(SolicitudEmergencia.id).label("total")).join(
                Zona, SolicitudEmergencia.zona_id == Zona.id, isouter=True
            )
        )
        .group_by(Zona.nombre)
        .order_by(func.count(SolicitudEmergencia.id).desc())
        .limit(10)
    )
    rows_zona = (await db.execute(q_zona)).all()
    zonas = [ZonaIncidencia(zona=(r.nombre or "Sin zona"), total=int(r.total)) for r in rows_zona]

    q_ef = (
        base_filter(
            select(
                Taller.id.label("taller_id"),
                Taller.nombre_comercial,
                func.avg(
                    _epoch_diff_minutes(SolicitudEmergencia.finalizada_at, SolicitudEmergencia.reportado_en)
                ).label("avg_min"),
                func.count(SolicitudEmergencia.id).label("total"),
            ).join(Taller, SolicitudEmergencia.taller_id == Taller.id)
        )
        .where(SolicitudEmergencia.finalizada_at.isnot(None))
        .group_by(Taller.id, Taller.nombre_comercial)
        .order_by(text("avg_min ASC"))
        .limit(10)
    )
    rows_ef = (await db.execute(q_ef)).all()
    eficientes = [
        TallerEficiente(
            taller_id=r.taller_id,
            nombre_comercial=r.nombre_comercial,
            tiempo_promedio_min=round(float(r.avg_min), 1),
            total_atendidos=int(r.total),
        )
        for r in rows_ef
    ]

    return KpiSummaryRead(
        tiempo_promedio_asignacion_min=round(float(tiempo_asig), 1) if tiempo_asig is not None else None,
        tiempo_promedio_llegada_min=round(float(tiempo_llegada), 1) if tiempo_llegada is not None else None,
        tiempo_promedio_atencion_min=round(float(tiempo_total), 1) if tiempo_total is not None else None,
        incidentes_activos=activos,
        incidentes_finalizados=finalizados,
        incidentes_cancelados=cancelados,
        cumplimiento_sla_pct=sla_pct,
        incidentes_por_tipo=por_tipo,
        zonas_con_mas_incidentes=zonas,
        talleres_mas_eficientes=eficientes,
    )
