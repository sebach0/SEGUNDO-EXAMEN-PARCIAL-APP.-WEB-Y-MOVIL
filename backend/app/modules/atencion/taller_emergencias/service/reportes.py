# Historial, comisiones y dashboard (CU30–CU31, reporte taller).
from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.atencion.taller_emergencias import repository
from app.modules.atencion.taller_emergencias.schemas import (
    ComisionTallerRead,
    HistorialAtencionRead,
    ReporteTallerDashboardRead,
    ReporteTecnicoGananciasRead,
    ResumenComisionesRead,
)
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum


async def listar_historial_atenciones(
    taller_id: int,
    db: AsyncSession,
    *,
    estado: EstadoSolicitudSeguimientoEnum | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = 200,
) -> list[HistorialAtencionRead]:
    """CU30 — solo solicitudes del taller (taller_id explícito en consulta)."""
    lim = max(1, min(limit, 500))
    desde_dt = datetime.combine(desde, time.min) if desde is not None else None
    hasta_dt = datetime.combine(hasta, time(23, 59, 59)) if hasta is not None else None
    rows = await repository.list_historial_atenciones_taller(
        db,
        taller_id=taller_id,
        estado=estado,
        desde=desde_dt,
        hasta=hasta_dt,
        limit=lim,
    )
    return [HistorialAtencionRead.model_validate(r) for r in rows]


async def listar_comisiones_taller(taller_id: int, db: AsyncSession) -> list[ComisionTallerRead]:
    """CU31 — detalle con join opcional a pagos + desglose de ítems de cotización."""
    from sqlalchemy import select as _sel
    from sqlalchemy.orm import selectinload as _sil
    from app.modules.cotizaciones.models import Cotizacion, CotizacionItem, EstadoCotizacionEnum

    rows = await repository.list_comisiones_taller_con_pago(db, taller_id=taller_id)
    comisiones = [ComisionTallerRead.model_validate(r) for r in rows]

    if not comisiones:
        return comisiones

    sol_ids = [c.solicitud_id for c in comisiones]
    res = await db.execute(
        _sel(Cotizacion)
        .options(_sil(Cotizacion.items))
        .where(
            Cotizacion.solicitud_id.in_(sol_ids),
            Cotizacion.estado == EstadoCotizacionEnum.ACEPTADA,
        )
    )
    cots_by_sol: dict[int, Cotizacion] = {cot.solicitud_id: cot for cot in res.scalars().all()}

    from app.modules.atencion.taller_emergencias.schemas import ItemDesgloseCotizacionRead
    for com in comisiones:
        cot = cots_by_sol.get(com.solicitud_id)
        if cot and cot.items:
            com.cotizacion_items = [
                ItemDesgloseCotizacionRead(
                    descripcion=item.descripcion,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal=item.subtotal,
                )
                for item in cot.items
            ]

    return comisiones


async def obtener_resumen_comisiones(taller_id: int, db: AsyncSession) -> ResumenComisionesRead:
    """CU31 — totales por taller."""
    row = await repository.resumen_comisiones_taller(db, taller_id=taller_id)
    return ResumenComisionesRead.model_validate(row)


async def obtener_reporte_dashboard_taller(
    taller_id: int,
    db: AsyncSession,
    *,
    desde: date | None = None,
    hasta: date | None = None,
) -> ReporteTallerDashboardRead:
    """
    KPIs: comisiones en rango, reparto neto por técnico, conteo de solicitudes por estado,
    bandeja pendiente.
    """
    desde_dt = datetime.combine(desde, time.min) if desde is not None else None
    hasta_dt = datetime.combine(hasta, time(23, 59, 59)) if hasta is not None else None

    res_row = await repository.resumen_comisiones_taller_rango(
        db, taller_id=taller_id, desde=desde_dt, hasta=hasta_dt
    )
    resumen = ResumenComisionesRead.model_validate(res_row)

    tec_rows = await repository.agregado_montos_por_tecnico(
        db, taller_id=taller_id, desde=desde_dt, hasta=hasta_dt
    )
    por_tecnico = [ReporteTecnicoGananciasRead.model_validate(r) for r in tec_rows]

    estado_rows = await repository.contar_solicitudes_por_estado_taller(
        db, taller_id=taller_id, desde=desde_dt, hasta=hasta_dt
    )
    solicitudes_por_estado = {e.value: n for e, n in estado_rows}

    bandeja_pend = await repository.contar_bandeja_pendientes_taller(db, taller_id=taller_id)

    return ReporteTallerDashboardRead(
        taller_id=taller_id,
        periodo_desde=desde,
        periodo_hasta=hasta,
        resumen_comisiones=resumen,
        bandeja_pendientes=bandeja_pend,
        solicitudes_por_estado=solicitudes_por_estado,
        ganancias_por_tecnico=por_tecnico,
    )
