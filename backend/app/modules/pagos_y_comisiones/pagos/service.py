# Lógica CU20 — pagos por solicitud; solo solicitudes propias del cliente.
from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal

import anyio
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notificaciones_service
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum
from app.modules.pagos_y_comisiones.pagos import repository
from app.modules.pagos_y_comisiones.pagos.gateway import PasarelaSimulada
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, MetodoPagoEnum
from app.modules.pagos_y_comisiones.pagos.schemas import PagoIniciadoRead, PagoRead, PagoSolicitudCreateIn, PagoStripeConfirmIn
from app.modules.pagos_y_comisiones.pagos import stripe_client
from app.modules.acceso_y_administracion.usuarios.models import Usuario

_log = logging.getLogger(__name__)

_ESTADOS_SOLICITUD_PAGABLES = frozenset(
    {
        EstadoSolicitudSeguimientoEnum.EN_ATENCION,
        EstadoSolicitudSeguimientoEnum.FINALIZADA,
    }
)

_MAX_MONTO = Decimal("99999999.99")


def _quantize_monto(m: Decimal) -> Decimal:
    return m.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _assert_solicitud_pagable(sol) -> None:
    if sol.estado not in _ESTADOS_SOLICITUD_PAGABLES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La solicitud no admite pago en su estado actual "
                f"({sol.estado.value}). Permitido cuando está en atención o finalizada."
            ),
        )


def _monto_a_unidad_menor(monto: Decimal) -> int:
    """Stripe: monto en unidad menor (p. ej. centavos para BOB)."""
    return int((monto * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


async def _aplicar_resultado_pasarela(
    db: AsyncSession,
    *,
    user: Usuario,
    solicitud,
    pago,
    resultado,
) -> None:
    now = utc_now_naive()
    if resultado.exitoso:
        pago.estado = EstadoPagoEnum.PAGADO
        pago.referencia_externa = resultado.referencia_externa
        pago.pagado_at = now
        pago.metadata_json = resultado.metadata
        await registrar_accion(
            db,
            "pagos",
            "pagos",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=f"Pago confirmado solicitud_id={pago.solicitud_id} ref={resultado.referencia_externa}",
            usuario_id=user.id,
            entidad_id=pago.id,
        )
        await notificaciones_service.notificar_cliente_solicitud_emergencia(
            db,
            solicitud=solicitud,
            tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
            titulo="Pago confirmado",
            mensaje="Tu pago fue confirmado correctamente. Gracias por usar la plataforma.",
        )
        await repository.registrar_comision_taller_tras_pago(db, solicitud=solicitud, pago=pago)
    else:
        pago.estado = EstadoPagoEnum.FALLIDO
        base = dict(resultado.metadata or {})
        if resultado.mensaje_error:
            base["error"] = resultado.mensaje_error
        pago.metadata_json = base
        await registrar_accion(
            db,
            "pagos",
            "pagos",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=f"Pago fallido solicitud_id={pago.solicitud_id}: {resultado.mensaje_error}",
            usuario_id=user.id,
            entidad_id=pago.id,
        )


def _pago_iniciado_desde_row(
    pago,
    *,
    stripe_client_secret: str | None = None,
    stripe_publishable_key: str | None = None,
) -> PagoIniciadoRead:
    base = PagoRead.model_validate(pago)
    return PagoIniciadoRead(
        **base.model_dump(),
        stripe_client_secret=stripe_client_secret,
        stripe_publishable_key=stripe_publishable_key,
    )


async def listar_pagos_solicitud(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    db: AsyncSession,
) -> list[PagoRead]:
    sol = await repository.get_solicitud_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    rows = await repository.list_pagos_solicitud(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    return [PagoRead.model_validate(x) for x in rows]


async def crear_pago_solicitud(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    body: PagoSolicitudCreateIn,
    db: AsyncSession,
) -> PagoIniciadoRead:
    sol = await repository.get_solicitud_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    _assert_solicitud_pagable(sol)

    ya_pagado = await repository.count_pagos_pagados_solicitud(db, solicitud_id=solicitud_id)
    if ya_pagado > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta solicitud ya tiene un pago confirmado.",
        )

    monto = _quantize_monto(body.monto)
    if monto > _MAX_MONTO:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Monto fuera de rango permitido.")

    if sol.presupuesto_bob is not None and sol.presupuesto_bob > 0:
        esperado = _quantize_monto(sol.presupuesto_bob)
        if monto != esperado:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El monto debe ser el presupuesto acordado: {esperado} BOB.",
            )

    now = utc_now_naive()
    # Stripe (PaymentIntent + PaymentSheet) solo aplica a tarjeta. Otros métodos usan flujo simulado / comprobación manual.
    usar_stripe_tarjeta = (
        bool(settings.stripe_enabled and settings.STRIPE_SECRET_KEY)
        and body.metodo == MetodoPagoEnum.TARJETA
    )
    proveedor = "STRIPE" if usar_stripe_tarjeta else settings.PAGO_PROVEEDOR_DEFAULT

    try:
        pago = await repository.insert_pago(
            db,
            solicitud_id=solicitud_id,
            cliente_id=cliente_id,
            monto=monto,
            moneda=body.moneda,
            metodo=body.metodo,
            estado=EstadoPagoEnum.PENDIENTE,
            proveedor=proveedor,
            created_at=now,
        )
        await registrar_accion(
            db,
            "pagos",
            "pagos",
            AccionBitacoraEnum.CREAR,
            descripcion=f"Inicio pago solicitud_id={solicitud_id} monto={monto} {body.moneda} proveedor={proveedor}",
            usuario_id=user.id,
            entidad_id=pago.id,
        )

        if usar_stripe_tarjeta:
            amount_minor = _monto_a_unidad_menor(monto)
            if amount_minor < 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Monto demasiado bajo para Stripe.",
                )
            try:
                pi = await anyio.to_thread.run_sync(
                    lambda: stripe_client.crear_payment_intent(
                        secret_key=settings.STRIPE_SECRET_KEY.strip(),
                        amount_minor_units=amount_minor,
                        currency=body.moneda,
                        metadata={
                            "solicitud_id": str(solicitud_id),
                            "pago_id": str(pago.id),
                            "cliente_id": str(cliente_id),
                        },
                    )
                )
            except Exception as e:
                _log.exception("Stripe PaymentIntent falló")
                pago.estado = EstadoPagoEnum.FALLIDO
                pago.metadata_json = {"stripe_error": str(e), "stripe": True}
                await repository.refresh_pago(db, pago)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="No se pudo iniciar el cobro con Stripe. Revisá credenciales y moneda.",
                ) from e

            pago.referencia_externa = pi["id"]
            pago.metadata_json = {
                "stripe": True,
                "payment_intent_id": pi["id"],
                "payment_intent_status": pi.get("status"),
            }
            await repository.refresh_pago(db, pago)
            return _pago_iniciado_desde_row(
                pago,
                stripe_client_secret=pi.get("client_secret"),
                stripe_publishable_key=(settings.STRIPE_PUBLISHABLE_KEY or "").strip() or None,
            )

        if settings.PAGO_SIMULADO_AUTOCOMPLETE:
            gw = PasarelaSimulada()
            res = await gw.ejecutar_cobro(
                pago_id=pago.id,
                solicitud_id=solicitud_id,
                monto=monto,
                moneda=pago.moneda,
                metodo=body.metodo.value,
            )
            await _aplicar_resultado_pasarela(
                db,
                user=user,
                solicitud=sol,
                pago=pago,
                resultado=res,
            )
        await repository.refresh_pago(db, pago)
        return _pago_iniciado_desde_row(pago)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar el pago (posible duplicado o restricción de integridad).",
        ) from None


async def completar_pago_simulado(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    pago_id: int,
    db: AsyncSession,
) -> PagoRead:
    """Confirma un pago **PENDIENTE** vía pasarela simulada (útil si PAGO_SIMULADO_AUTOCOMPLETE=false)."""

    sol = await repository.get_solicitud_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    pago = await repository.get_pago_solicitud_cliente(
        db, pago_id=pago_id, solicitud_id=solicitud_id, cliente_id=cliente_id
    )
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")

    if pago.proveedor.strip().upper() == "STRIPE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pago es Stripe: usá POST .../pagos/{id}/confirmar-stripe tras el SDK.",
        )

    if pago.estado == EstadoPagoEnum.PAGADO:
        return PagoRead.model_validate(pago)
    if pago.estado != EstadoPagoEnum.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El pago no puede completarse en estado {pago.estado.value}.",
        )

    try:
        gw = PasarelaSimulada()
        res = await gw.ejecutar_cobro(
            pago_id=pago.id,
            solicitud_id=solicitud_id,
            monto=pago.monto,
            moneda=pago.moneda,
            metodo=pago.metodo.value,
        )
        await _aplicar_resultado_pasarela(
            db,
            user=user,
            solicitud=sol,
            pago=pago,
            resultado=res,
        )
        await repository.refresh_pago(db, pago)
        return PagoRead.model_validate(pago)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo confirmar el pago (posible conflicto con otro cobro).",
        ) from None


async def confirmar_pago_stripe(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    pago_id: int,
    body: PagoStripeConfirmIn,
    db: AsyncSession,
) -> PagoRead:
    """Marca **PAGADO** si el PaymentIntent en Stripe está en ``succeeded``."""

    if not settings.stripe_enabled or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no está configurado en el servidor.",
        )

    sol = await repository.get_solicitud_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    pago = await repository.get_pago_solicitud_cliente(
        db, pago_id=pago_id, solicitud_id=solicitud_id, cliente_id=cliente_id
    )
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")

    if pago.proveedor.strip().upper() != "STRIPE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pago no fue creado con Stripe.",
        )

    if pago.estado == EstadoPagoEnum.PAGADO:
        return PagoRead.model_validate(pago)

    pi_id = (body.payment_intent_id or pago.referencia_externa or "").strip()
    if not pi_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Falta payment_intent_id.")

    if pago.referencia_externa and pi_id != pago.referencia_externa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El PaymentIntent no coincide con el registro de pago.",
        )

    try:
        pi = await anyio.to_thread.run_sync(
            lambda: stripe_client.obtener_payment_intent(
                secret_key=settings.STRIPE_SECRET_KEY.strip(),
                payment_intent_id=pi_id,
            )
        )
    except Exception as e:
        _log.exception("Stripe retrieve falló")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo consultar el estado en Stripe.",
        ) from e

    if pi.get("status") != "succeeded":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PaymentIntent en estado {pi.get('status')!r}; el cobro aún no está confirmado.",
        )

    now = utc_now_naive()
    pago.estado = EstadoPagoEnum.PAGADO
    pago.pagado_at = now
    meta = dict(pago.metadata_json or {})
    meta["stripe"] = True
    meta["payment_intent_status"] = "succeeded"
    pago.metadata_json = meta

    await registrar_accion(
        db,
        "pagos",
        "pagos",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Pago Stripe confirmado solicitud_id={solicitud_id} pi={pi_id}",
        usuario_id=user.id,
        entidad_id=pago.id,
    )
    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=sol,
        tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
        titulo="Pago confirmado",
        mensaje="Tu pago en Stripe fue confirmado correctamente.",
    )
    await repository.registrar_comision_taller_tras_pago(db, solicitud=sol, pago=pago)
    await repository.refresh_pago(db, pago)
    return PagoRead.model_validate(pago)
