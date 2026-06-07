# Admin — listado y validación manual de pagos (CU49 / Ciclo 5).
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.deps import resolve_tenant_scope
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notificaciones_service
from app.modules.cotizaciones.tenant_guard import assert_user_tenant_access
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.pagos_y_comisiones.pagos import repository
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, MetodoPagoEnum, Pago
from app.modules.pagos_y_comisiones.pagos.schemas import AdminPagoListRead, PagoRead, PagoValidateManualIn

_METODOS_MANUALES = frozenset({MetodoPagoEnum.TRANSFERENCIA, MetodoPagoEnum.EFECTIVO, MetodoPagoEnum.OTRO})


async def list_pagos_admin(
    db: AsyncSession,
    *,
    user: Usuario,
    permisos: list[str],
    tenant_id: int | None,
    estado: EstadoPagoEnum | None,
    limit: int,
    offset: int,
) -> AdminPagoListRead:
    effective_tenant = resolve_tenant_scope(user, tenant_id, permisos)

    filters = [Pago.tenant_id == effective_tenant]
    if estado is not None:
        filters.append(Pago.estado == estado)

    count_q = select(func.count()).select_from(Pago).where(*filters)
    total = int((await db.execute(count_q)).scalar_one())

    rows_q = (
        select(Pago)
        .where(*filters)
        .order_by(Pago.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list((await db.execute(rows_q)).scalars().all())
    return AdminPagoListRead(items=[PagoRead.model_validate(r) for r in rows], total=total)


async def validate_manual_pago(
    db: AsyncSession,
    *,
    user: Usuario,
    permisos: list[str],
    pago_id: int,
    body: PagoValidateManualIn,
) -> PagoRead:
    res = await db.execute(select(Pago).where(Pago.id == pago_id).with_for_update())
    pago = res.scalar_one_or_none()
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")

    assert_user_tenant_access(user, pago.tenant_id, permisos)

    if pago.estado != EstadoPagoEnum.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se validan pagos PENDIENTE (actual: {pago.estado.value}).",
        )

    if pago.metodo not in _METODOS_MANUALES and pago.proveedor.strip().upper() != "MANUAL":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La validación manual aplica a transferencia, efectivo u otro método offline.",
        )

    res_sol = await db.execute(
        select(SolicitudEmergencia).where(SolicitudEmergencia.id == pago.solicitud_id)
    )
    sol = res_sol.scalar_one_or_none()
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    now = utc_now_naive()
    meta = dict(pago.metadata_json or {})
    if body.observacion:
        meta["validacion_manual_obs"] = body.observacion
    meta["validado_por_usuario_id"] = user.id

    if body.aprobado:
        ya_pagado = await repository.count_pagos_pagados_solicitud(db, solicitud_id=pago.solicitud_id)
        if ya_pagado > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La solicitud ya tiene un pago confirmado.",
            )
        pago.estado = EstadoPagoEnum.PAGADO
        pago.pagado_at = now
        pago.conciliado_at = now
        pago.metadata_json = meta
        await registrar_accion(
            db,
            "pagos",
            "pagos",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=f"Admin validó pago manual id={pago_id} solicitud_id={pago.solicitud_id}",
            usuario_id=user.id,
            entidad_id=pago.id,
        )
        await notificaciones_service.notificar_cliente_solicitud_emergencia(
            db,
            solicitud=sol,
            tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
            titulo="Pago confirmado",
            mensaje="Tu pago fue validado por el administrador.",
        )
        await repository.registrar_comision_taller_tras_pago(db, solicitud=sol, pago=pago)
    else:
        pago.estado = EstadoPagoEnum.ANULADO
        meta["rechazado"] = True
        pago.metadata_json = meta
        await registrar_accion(
            db,
            "pagos",
            "pagos",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=f"Admin rechazó pago manual id={pago_id}",
            usuario_id=user.id,
            entidad_id=pago.id,
        )

    await db.flush()
    await repository.refresh_pago(db, pago)
    return PagoRead.model_validate(pago)
