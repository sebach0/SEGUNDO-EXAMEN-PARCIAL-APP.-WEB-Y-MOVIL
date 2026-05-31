from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.atencion.taller_emergencias.models import ComisionTaller, EstadoComisionTallerEnum
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, Pago

_log = logging.getLogger(__name__)

_PORCENTAJE_PLATAFORMA = Decimal("10.00")


def _quantize_monto(m: Decimal) -> Decimal:
    return m.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def get_solicitud_cliente(
    db: AsyncSession, *, solicitud_id: int, cliente_id: int
) -> SolicitudEmergencia | None:
    r = await db.execute(
        select(SolicitudEmergencia).where(
            SolicitudEmergencia.id == solicitud_id,
            SolicitudEmergencia.cliente_id == cliente_id,
        )
    )
    return r.scalar_one_or_none()


async def count_pagos_pagados_solicitud(db: AsyncSession, *, solicitud_id: int) -> int:
    r = await db.execute(
        select(func.count())
        .select_from(Pago)
        .where(Pago.solicitud_id == solicitud_id, Pago.estado == EstadoPagoEnum.PAGADO)
    )
    return int(r.scalar_one())


async def list_pagos_solicitud(db: AsyncSession, *, solicitud_id: int, cliente_id: int) -> list[Pago]:
    r = await db.execute(
        select(Pago)
        .where(Pago.solicitud_id == solicitud_id, Pago.cliente_id == cliente_id)
        .order_by(Pago.created_at.desc())
    )
    return list(r.scalars().all())


async def get_pago_solicitud_cliente(
    db: AsyncSession, *, pago_id: int, solicitud_id: int, cliente_id: int
) -> Pago | None:
    r = await db.execute(
        select(Pago).where(
            Pago.id == pago_id,
            Pago.solicitud_id == solicitud_id,
            Pago.cliente_id == cliente_id,
        )
    )
    return r.scalar_one_or_none()


async def insert_pago(
    db: AsyncSession,
    *,
    solicitud_id: int,
    cliente_id: int,
    monto,
    moneda: str,
    metodo,
    estado,
    proveedor: str,
    created_at,
) -> Pago:
    row = Pago(
        solicitud_id=solicitud_id,
        cliente_id=cliente_id,
        monto=monto,
        moneda=moneda,
        metodo=metodo,
        estado=estado,
        proveedor=proveedor,
        created_at=created_at,
    )
    db.add(row)
    await db.flush()
    return row


async def refresh_pago(db: AsyncSession, pago: Pago) -> None:
    await db.refresh(pago)


async def get_comision_taller_por_solicitud(
    db: AsyncSession, *, solicitud_id: int
) -> ComisionTaller | None:
    r = await db.execute(select(ComisionTaller).where(ComisionTaller.solicitud_id == solicitud_id))
    return r.scalar_one_or_none()


async def registrar_comision_taller_tras_pago(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    pago: Pago,
) -> None:
    """
    Crea fila en comisiones_taller cuando un pago queda PAGADO (CU31 / dashboard ganancias).
    Idempotente: si ya existe comisión para la solicitud, no duplica.
    """
    if pago.estado != EstadoPagoEnum.PAGADO:
        return
    if solicitud.taller_id is None:
        _log.warning(
            "Omitiendo comisión: solicitud %s no tiene taller_id (pago %s).",
            solicitud.id,
            pago.id,
        )
        return
    existing = await get_comision_taller_por_solicitud(db, solicitud_id=solicitud.id)
    if existing is not None:
        return

    monto = _quantize_monto(pago.monto)
    com = (monto * (_PORCENTAJE_PLATAFORMA / Decimal("100"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    neto = (monto - com).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    when = pago.pagado_at or utc_now_naive()
    row = ComisionTaller(
        solicitud_id=solicitud.id,
        taller_id=solicitud.taller_id,
        pago_id=pago.id,
        porcentaje_plataforma=_PORCENTAJE_PLATAFORMA,
        monto_servicio=monto,
        monto_comision=com,
        monto_taller_neto=neto,
        estado=EstadoComisionTallerEnum.CALCULADA,
        calculado_at=when,
        liquidado_at=None,
    )
    db.add(row)
    await db.flush()
