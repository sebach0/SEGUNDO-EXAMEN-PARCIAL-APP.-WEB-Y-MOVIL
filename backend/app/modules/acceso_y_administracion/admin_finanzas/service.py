from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import Date, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.atencion.taller_emergencias.models import ComisionTaller
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, SolicitudEmergencia
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, Pago
from app.modules.talleres_y_tecnicos.talleres.models import Taller

PORCENTAJE_PLATAFORMA = Decimal("10.00")
MONEDA = "BOB"
_D2 = Decimal("0.01")


def _d(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        base = value
    elif value is None:
        base = Decimal("0")
    else:
        base = Decimal(str(value))
    return base.quantize(_D2, rounding=ROUND_HALF_UP)


def _tasa(numerador: int, denominador: int) -> Decimal:
    if denominador <= 0:
        return Decimal("0.00")
    return _d((Decimal(numerador) / Decimal(denominador)) * Decimal("100"))


async def get_finanzas_resumen(
    db: AsyncSession,
    *,
    desde: datetime | None,
    hasta: datetime | None,
) -> dict[str, Any]:
    c_filters = []
    p_filters = [Pago.estado == EstadoPagoEnum.PAGADO]
    s_filters = [SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum.FINALIZADA]

    if desde:
        c_filters.append(ComisionTaller.calculado_at >= desde)
        p_filters.append(Pago.pagado_at >= desde)
        s_filters.append(SolicitudEmergencia.finalizada_at >= desde)
    if hasta:
        c_filters.append(ComisionTaller.calculado_at <= hasta)
        p_filters.append(Pago.pagado_at <= hasta)
        s_filters.append(SolicitudEmergencia.finalizada_at <= hasta)

    com_q = select(
        func.count(ComisionTaller.id).label("n_comisiones"),
        func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_monto_servicio"),
        func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_comision_plataforma"),
        func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_neto_taller"),
        func.count(distinct(ComisionTaller.taller_id)).label("n_talleres_con_comision"),
    )
    if c_filters:
        com_q = com_q.where(*c_filters)
    com_row = (await db.execute(com_q)).mappings().one()

    pagos_q = select(
        func.count(Pago.id).label("n_pagos_pagados"),
        func.coalesce(func.sum(Pago.monto), 0).label("total_monto_pagos"),
    ).where(*p_filters)
    pagos_row = (await db.execute(pagos_q)).mappings().one()

    solicitudes_q = select(func.count(SolicitudEmergencia.id).label("n_solicitudes_finalizadas")).where(*s_filters)
    solicitudes_row = (await db.execute(solicitudes_q)).mappings().one()

    por_taller_q = (
        select(
            ComisionTaller.taller_id.label("taller_id"),
            Taller.nombre_comercial.label("nombre_comercial"),
            func.count(ComisionTaller.id).label("n_comisiones"),
            func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_monto_servicio"),
            func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_comision_plataforma"),
            func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_neto_taller"),
        )
        .join(Taller, Taller.id == ComisionTaller.taller_id)
        .group_by(ComisionTaller.taller_id, Taller.nombre_comercial)
        .order_by(func.sum(ComisionTaller.monto_comision).desc().nulls_last())
    )
    if c_filters:
        por_taller_q = por_taller_q.where(*c_filters)
    por_taller = [(dict(r)) for r in (await db.execute(por_taller_q)).mappings().all()]

    n_pagos_pagados = int(pagos_row["n_pagos_pagados"] or 0)
    total_monto_pagos = _d(pagos_row["total_monto_pagos"])
    ticket_promedio = _d(total_monto_pagos / Decimal(n_pagos_pagados)) if n_pagos_pagados else Decimal("0.00")
    n_solicitudes_finalizadas = int(solicitudes_row["n_solicitudes_finalizadas"] or 0)

    return {
        "porcentaje_plataforma": PORCENTAJE_PLATAFORMA,
        "moneda": MONEDA,
        "desde": desde,
        "hasta": hasta,
        "n_comisiones": int(com_row["n_comisiones"] or 0),
        "total_monto_servicio": _d(com_row["total_monto_servicio"]),
        "total_comision_plataforma": _d(com_row["total_comision_plataforma"]),
        "total_neto_taller": _d(com_row["total_neto_taller"]),
        "n_pagos_pagados": n_pagos_pagados,
        "total_monto_pagos": total_monto_pagos,
        "n_solicitudes_finalizadas": n_solicitudes_finalizadas,
        "n_talleres_con_comision": int(com_row["n_talleres_con_comision"] or 0),
        "ticket_promedio_pagado": ticket_promedio,
        "tasa_conversion_pago_pct": _tasa(n_pagos_pagados, n_solicitudes_finalizadas),
        "por_taller": [
            {
                **x,
                "total_monto_servicio": _d(x["total_monto_servicio"]),
                "total_comision_plataforma": _d(x["total_comision_plataforma"]),
                "total_neto_taller": _d(x["total_neto_taller"]),
            }
            for x in por_taller
        ],
    }


async def get_finanzas_reportes(
    db: AsyncSession,
    *,
    desde: datetime | None,
    hasta: datetime | None,
) -> dict[str, Any]:
    resumen = await get_finanzas_resumen(db, desde=desde, hasta=hasta)

    filters = []
    if desde:
        filters.append(ComisionTaller.calculado_at >= desde)
    if hasta:
        filters.append(ComisionTaller.calculado_at <= hasta)

    serie_q = (
        select(
            cast(ComisionTaller.calculado_at, Date).label("fecha"),
            func.count(ComisionTaller.id).label("n_comisiones"),
            func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_monto_servicio"),
            func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_comision_plataforma"),
            func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_neto_taller"),
        )
        .group_by(cast(ComisionTaller.calculado_at, Date))
        .order_by(cast(ComisionTaller.calculado_at, Date).asc())
    )
    if filters:
        serie_q = serie_q.where(*filters)
    serie_rows = (await db.execute(serie_q)).mappings().all()

    serie_diaria = [
        {
            "fecha": row["fecha"],
            "n_comisiones": int(row["n_comisiones"] or 0),
            "total_monto_servicio": _d(row["total_monto_servicio"]),
            "total_comision_plataforma": _d(row["total_comision_plataforma"]),
            "total_neto_taller": _d(row["total_neto_taller"]),
        }
        for row in serie_rows
    ]

    return {
        "resumen": resumen,
        "top_talleres": resumen["por_taller"][:5],
        "serie_diaria": serie_diaria,
    }

