# Reportes operativos desde solicitudes_emergencia (CU46).
from __future__ import annotations

import csv
import io

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.clientes_y_vehiculos.vehiculos.models import Vehiculo
from app.modules.ciclo4.incidentes.models import Zona
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.kpis.filters import KpiFilters, apply_solicitud_filters, llegada_efectiva_col, tipo_incidente_col
from app.modules.kpis import service as kpi_service
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, Pago
from app.modules.reports.schemas import (
    CancellationReportRead,
    IncidentReportRead,
    IncidentReportRow,
    PerformanceReportRead,
    ReportTotals,
    WorkshopReportRead,
    WorkshopReportRow,
)
from app.modules.talleres_y_tecnicos.talleres.models import Taller


def _epoch_diff_minutes(col_end, col_start):
    return func.extract("epoch", col_end - col_start) / 60.0


def _empty_message(total: int) -> str | None:
    return "Sin resultados para los filtros indicados." if total == 0 else None


def _base_incident_query(filters: KpiFilters, *, estado=None):
    llegada = llegada_efectiva_col()
    tipo_col = tipo_incidente_col()
    q = apply_solicitud_filters(
        select(
            SolicitudEmergencia.id.label("solicitud_id"),
            SolicitudEmergencia.estado,
            SolicitudEmergencia.reportado_en,
            SolicitudEmergencia.asignado_en,
            SolicitudEmergencia.en_atencion_en,
            SolicitudEmergencia.finalizada_at,
            SolicitudEmergencia.sla_minutos,
            tipo_col.label("tipo_incidente"),
            Zona.nombre.label("zona"),
            Taller.nombre_comercial.label("taller"),
            Vehiculo.placa.label("vehiculo_placa"),
            Usuario.nombres,
            Usuario.apellidos,
            _epoch_diff_minutes(SolicitudEmergencia.asignado_en, SolicitudEmergencia.reportado_en).label(
                "min_asig"
            ),
            _epoch_diff_minutes(llegada, SolicitudEmergencia.asignado_en).label("min_llegada"),
        )
        .join(Cliente, SolicitudEmergencia.cliente_id == Cliente.id)
        .join(Usuario, Cliente.usuario_id == Usuario.id)
        .join(Vehiculo, SolicitudEmergencia.vehiculo_id == Vehiculo.id)
        .join(Taller, SolicitudEmergencia.taller_id == Taller.id, isouter=True)
        .join(Zona, SolicitudEmergencia.zona_id == Zona.id, isouter=True),
        filters,
    )
    if estado is not None:
        q = q.where(SolicitudEmergencia.estado == estado)
    q = q.order_by(SolicitudEmergencia.reportado_en.desc().nullslast()).limit(500)
    return q


async def _monto_pagado_map(db: AsyncSession, solicitud_ids: list[int]) -> dict[int, float]:
    if not solicitud_ids:
        return {}
    q = (
        select(Pago.solicitud_id, func.max(Pago.monto))
        .where(
            Pago.solicitud_id.in_(solicitud_ids),
            Pago.estado == EstadoPagoEnum.PAGADO,
        )
        .group_by(Pago.solicitud_id)
    )
    rows = (await db.execute(q)).all()
    return {int(sid): float(monto) for sid, monto in rows}


def _row_from_result(r, pagos: dict[int, float]) -> IncidentReportRow:
    min_asig = round(float(r.min_asig), 1) if r.min_asig is not None else None
    min_lleg = round(float(r.min_llegada), 1) if r.min_llegada is not None else None
    cumple: bool | None = None
    if r.finalizada_at and r.reportado_en and r.sla_minutos is not None and min_asig is not None:
        total_min = (
            (r.finalizada_at - r.reportado_en).total_seconds() / 60.0
            if r.finalizada_at and r.reportado_en
            else None
        )
        if total_min is not None:
            cumple = total_min <= float(r.sla_minutos)
    cliente = f"{r.nombres} {r.apellidos}".strip() if r.nombres else None
    return IncidentReportRow(
        solicitud_id=r.solicitud_id,
        cliente=cliente,
        vehiculo_placa=r.vehiculo_placa,
        tipo_incidente=r.tipo_incidente,
        zona=r.zona,
        taller=r.taller,
        estado=r.estado.value if hasattr(r.estado, "value") else str(r.estado),
        reportado_en=r.reportado_en,
        asignado_en=r.asignado_en,
        en_atencion_en=r.en_atencion_en,
        finalizado_en=r.finalizada_at,
        minutos_asignacion=min_asig,
        minutos_llegada=min_lleg,
        cumple_sla=cumple,
        monto_pagado=pagos.get(r.solicitud_id),
    )


async def get_incidents_report(
    db: AsyncSession,
    filters: KpiFilters,
    *,
    estado=None,
) -> IncidentReportRead:
    q = _base_incident_query(filters, estado=estado)
    rows = (await db.execute(q)).all()
    ids = [r.solicitud_id for r in rows]
    pagos = await _monto_pagado_map(db, ids)
    items = [_row_from_result(r, pagos) for r in rows]

    _, finalizados, cancelados = await kpi_service.get_counts(db, filters)
    q_total = apply_solicitud_filters(select(func.count(SolicitudEmergencia.id)), filters)
    total = int((await db.execute(q_total)).scalar() or 0)

    return IncidentReportRead(
        items=items,
        totals=ReportTotals(
            total=total,
            finalizados=finalizados,
            cancelados=cancelados,
            cumplimiento_sla_pct=await kpi_service.get_sla_compliance_pct(db, filters),
        ),
        message=_empty_message(len(items)),
    )


async def get_performance_report(db: AsyncSession, filters: KpiFilters) -> PerformanceReportRead:
    q_total = apply_solicitud_filters(select(func.count(SolicitudEmergencia.id)), filters)
    total = int((await db.execute(q_total)).scalar() or 0)
    return PerformanceReportRead(
        promedio_asignacion_min=await kpi_service.get_average_assignment_minutes(db, filters),
        promedio_llegada_min=await kpi_service.get_average_arrival_minutes(db, filters),
        promedio_total_min=await kpi_service.get_average_total_minutes(db, filters),
        cumplimiento_sla_pct=await kpi_service.get_sla_compliance_pct(db, filters),
        total_incidentes=total,
        message=_empty_message(total),
    )


async def get_workshops_report(db: AsyncSession, filters: KpiFilters) -> WorkshopReportRead:
    llegada = llegada_efectiva_col()
    q = (
        apply_solicitud_filters(
            select(
                Taller.id.label("taller_id"),
                Taller.nombre_comercial,
                func.count(SolicitudEmergencia.id).label("total"),
                func.count(
                    case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.FINALIZADA, 1))
                ).label("finalizados"),
                func.count(
                    case((SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.CANCELADA, 1))
                ).label("cancelados"),
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
                ).label("cumple_sla"),
                func.count(case((SolicitudEmergencia.finalizada_at.isnot(None), 1))).label("total_fin"),
            ).join(Taller, SolicitudEmergencia.taller_id == Taller.id),
            filters,
        )
        .group_by(Taller.id, Taller.nombre_comercial)
        .order_by(func.count(SolicitudEmergencia.id).desc())
    )
    rows = (await db.execute(q)).all()
    items: list[WorkshopReportRow] = []
    for r in rows:
        sla_pct: float | None = None
        if r.total_fin and r.total_fin > 0:
            sla_pct = round(float(r.cumple_sla or 0) / float(r.total_fin) * 100, 1)
        items.append(
            WorkshopReportRow(
                taller_id=r.taller_id,
                nombre_comercial=r.nombre_comercial,
                total_servicios=int(r.total),
                finalizados=int(r.finalizados or 0),
                cancelados=int(r.cancelados or 0),
                promedio_asignacion_min=round(float(r.avg_asig), 1) if r.avg_asig else None,
                promedio_llegada_min=round(float(r.avg_llegada), 1) if r.avg_llegada else None,
                cumplimiento_sla_pct=sla_pct,
            )
        )

    _, finalizados, cancelados = await kpi_service.get_counts(db, filters)
    q_total = apply_solicitud_filters(select(func.count(SolicitudEmergencia.id)), filters)
    total = int((await db.execute(q_total)).scalar() or 0)

    return WorkshopReportRead(
        items=items,
        totals=ReportTotals(
            total=total,
            finalizados=finalizados,
            cancelados=cancelados,
            cumplimiento_sla_pct=await kpi_service.get_sla_compliance_pct(db, filters),
        ),
        message=_empty_message(len(items)),
    )


async def get_cancellations_report(db: AsyncSession, filters: KpiFilters) -> CancellationReportRead:
    estado_enum = EstadoSolicitudSeguimientoEnum.CANCELADA
    rep = await get_incidents_report(db, filters, estado=estado_enum)
    return CancellationReportRead(
        items=rep.items,
        totals=ReportTotals(total=rep.totals.cancelados, cancelados=rep.totals.cancelados),
        message=rep.message,
    )


async def export_incidents_csv(db: AsyncSession, filters: KpiFilters) -> str:
    rep = await get_incidents_report(db, filters)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "solicitud_id",
            "cliente",
            "vehiculo_placa",
            "tipo_incidente",
            "zona",
            "taller",
            "estado",
            "reportado_en",
            "asignado_en",
            "finalizado_en",
            "minutos_asignacion",
            "minutos_llegada",
            "cumple_sla",
            "monto_pagado",
        ]
    )
    for row in rep.items:
        writer.writerow(
            [
                row.solicitud_id,
                row.cliente or "",
                row.vehiculo_placa or "",
                row.tipo_incidente or "",
                row.zona or "",
                row.taller or "",
                row.estado,
                row.reportado_en.isoformat() if row.reportado_en else "",
                row.asignado_en.isoformat() if row.asignado_en else "",
                row.finalizado_en.isoformat() if row.finalizado_en else "",
                row.minutos_asignacion if row.minutos_asignacion is not None else "",
                row.minutos_llegada if row.minutos_llegada is not None else "",
                row.cumple_sla if row.cumple_sla is not None else "",
                row.monto_pagado if row.monto_pagado is not None else "",
            ]
        )
    return buf.getvalue()
