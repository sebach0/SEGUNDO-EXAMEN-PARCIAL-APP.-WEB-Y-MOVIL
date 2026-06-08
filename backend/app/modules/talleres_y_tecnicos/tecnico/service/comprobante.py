from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.cotizaciones.models import Cotizacion, CotizacionItem, EstadoCotizacionEnum
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, MetodoPagoEnum, Pago
from app.modules.pagos_y_comisiones.pagos import repository as pagos_repository
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from .. import repository
from ..schemas import (
    ActualizarCotizacionTecnicoIn,
    ComprobanteTecnicoRead,
    ItemComprobanteRead,
    RegistrarCobroIn,
)
from .acceso import get_tecnico_row_for_usuario
from app.modules.pagos_y_comisiones.pagos.schemas import PagoRead

_ESTADOS_COBRO_PERMITIDOS = frozenset({
    EstadoSolicitudSeguimientoEnum.FINALIZADA,
})


def _quantize(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def get_comprobante(
    user: Usuario,
    solicitud_id: int,
    db: AsyncSession,
) -> ComprobanteTecnicoRead:
    t = await get_tecnico_row_for_usuario(user.id, db)

    # Datos base del servicio (vista con cliente + vehículo)
    row = await repository.get_servicio_asignado_detalle(db, solicitud_id=solicitud_id, tecnico_id=t.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    # Solicitud completa (finalizada_at)
    res_sol = await db.execute(
        select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id)
    )
    sol = res_sol.scalar_one()

    # Cotización aceptada con items
    res_cot = await db.execute(
        select(Cotizacion)
        .options(selectinload(Cotizacion.items))
        .where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.estado == EstadoCotizacionEnum.ACEPTADA,
        )
    )
    cot = res_cot.scalar_one_or_none()

    # Pago completado (si existe)
    res_pago = await db.execute(
        select(Pago)
        .where(Pago.solicitud_id == solicitud_id, Pago.estado == EstadoPagoEnum.PAGADO)
        .order_by(Pago.created_at.desc())
        .limit(1)
    )
    pago = res_pago.scalar_one_or_none()

    # Monto a cobrar: cotización > presupuesto_bob
    monto_a_cobrar: Decimal | None = None
    if cot is not None:
        monto_a_cobrar = _quantize(cot.monto_total)
    elif sol.presupuesto_bob is not None:
        monto_a_cobrar = _quantize(sol.presupuesto_bob)

    cliente_nombre = f"{row.get('nombres', '')} {row.get('apellidos', '')}".strip()
    partes_vehiculo = [
        row.get("placa") or "",
        row.get("marca") or "",
        row.get("modelo") or "",
    ]
    vehiculo_descripcion = " · ".join(p for p in partes_vehiculo if p)

    items: list[ItemComprobanteRead] = []
    if cot is not None:
        for item in cot.items:
            items.append(ItemComprobanteRead(
                descripcion=item.descripcion,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal,
            ))

    return ComprobanteTecnicoRead(
        solicitud_id=solicitud_id,
        estado=sol.estado,
        cliente_nombre=cliente_nombre,
        vehiculo_descripcion=vehiculo_descripcion,
        presupuesto_bob=sol.presupuesto_bob,
        cotizacion_id=cot.id if cot else None,
        cotizacion_descripcion_danio=cot.descripcion_danio if cot else None,
        cotizacion_monto_total=_quantize(cot.monto_total) if cot else None,
        cotizacion_items=items,
        monto_a_cobrar=monto_a_cobrar,
        pago_realizado=pago is not None,
        pago_estado=pago.estado if pago else None,
        pago_metodo=pago.metodo if pago else None,
        pago_monto=pago.monto if pago else None,
        pago_referencia=pago.referencia_externa if pago else None,
        pagado_at=pago.pagado_at if pago else None,
        finalizada_at=sol.finalizada_at,
    )


async def registrar_cobro_efectivo(
    user: Usuario,
    solicitud_id: int,
    body: RegistrarCobroIn,
    db: AsyncSession,
) -> PagoRead:
    t = await get_tecnico_row_for_usuario(user.id, db)

    res_sol = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .with_for_update()
    )
    sol = res_sol.scalar_one_or_none()
    if sol is None or sol.tecnico_id != t.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    if sol.estado not in _ESTADOS_COBRO_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede cobrar en estado '{sol.estado.value}'. "
                "El servicio debe estar En Atención o Finalizado."
            ),
        )

    # Verificar que no exista ya un pago completado
    ya_pagado = await pagos_repository.count_pagos_pagados_solicitud(db, solicitud_id=solicitud_id)
    if ya_pagado > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta solicitud ya tiene un pago registrado.",
        )

    # Determinar monto: cotización aceptada o presupuesto_bob
    res_cot = await db.execute(
        select(Cotizacion).where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.estado == EstadoCotizacionEnum.ACEPTADA,
        )
    )
    cot = res_cot.scalar_one_or_none()

    monto: Decimal | None = None
    cotizacion_id: int | None = None
    if cot is not None:
        monto = _quantize(cot.monto_total)
        cotizacion_id = cot.id
    elif sol.presupuesto_bob is not None and sol.presupuesto_bob > 0:
        monto = _quantize(sol.presupuesto_bob)

    if monto is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay monto definido para cobrar. Registrá un presupuesto antes de cobrar.",
        )

    now = utc_now_naive()
    pago = await pagos_repository.insert_pago(
        db,
        solicitud_id=solicitud_id,
        cliente_id=sol.cliente_id,
        monto=monto,
        moneda="BOB",
        metodo=body.metodo,
        estado=EstadoPagoEnum.PAGADO,
        proveedor="TECNICO_EFECTIVO",
        created_at=now,
        tenant_id=sol.tenant_id,
        cotizacion_id=cotizacion_id,
    )
    pago.pagado_at = now

    # Registrar comisión del taller
    await pagos_repository.registrar_comision_taller_tras_pago(db, solicitud=sol, pago=pago)

    await registrar_accion(
        db,
        "tecnico",
        "pagos",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Cobro {body.metodo.value} sol_id={solicitud_id} monto={monto}",
        usuario_id=user.id,
        entidad_id=pago.id,
    )

    return PagoRead.model_validate(pago)


async def actualizar_items_cotizacion(
    user: Usuario,
    solicitud_id: int,
    body: ActualizarCotizacionTecnicoIn,
    db: AsyncSession,
) -> ComprobanteTecnicoRead:
    """Reemplaza todos los ítems de la cotización aceptada (solo en EN_ATENCION, sin pago)."""
    t = await get_tecnico_row_for_usuario(user.id, db)

    res_sol = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .with_for_update()
    )
    sol = res_sol.scalar_one_or_none()
    if sol is None or sol.tecnico_id != t.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    if sol.estado != EstadoSolicitudSeguimientoEnum.EN_ATENCION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede editar la cotización cuando el servicio está En Atención.",
        )

    # Cotización aceptada (sin cargar items — usamos DELETE directo)
    res_cot = await db.execute(
        select(Cotizacion)
        .where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.estado == EstadoCotizacionEnum.ACEPTADA,
        )
    )
    cot = res_cot.scalar_one_or_none()
    if cot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay cotización aceptada para esta solicitud.",
        )

    ya_pagado = await pagos_repository.count_pagos_pagados_solicitud(db, solicitud_id=solicitud_id)
    if ya_pagado > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede modificar la cotización: ya existe un pago registrado.",
        )

    if not body.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cotización debe tener al menos un ítem.",
        )

    # Borrar ítems existentes con DELETE directo (evita lazy-load en sesión async)
    await db.execute(sa_delete(CotizacionItem).where(CotizacionItem.cotizacion_id == cot.id))

    # Insertar nuevos ítems y calcular total
    nuevo_total = Decimal("0")
    for item_in in body.items:
        subtotal = _quantize(item_in.cantidad * item_in.precio_unitario)
        nuevo_total += subtotal
        db.add(CotizacionItem(
            cotizacion_id=cot.id,
            tenant_id=cot.tenant_id,
            descripcion=item_in.descripcion,
            cantidad=item_in.cantidad,
            precio_unitario=item_in.precio_unitario,
        ))

    cot.monto_total = _quantize(nuevo_total)
    cot.actualizado_at = utc_now_naive()

    await db.flush()

    await registrar_accion(
        db,
        "tecnico",
        "cotizaciones",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=(
            f"Edición ítems cot_id={cot.id} sol_id={solicitud_id} "
            f"items={len(body.items)} total={nuevo_total}"
        ),
        usuario_id=user.id,
        entidad_id=cot.id,
    )

    return await get_comprobante(user, solicitud_id, db)
