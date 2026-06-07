"""
CU20 — Pagos del servicio (cliente autenticado).

Rutas bajo el mismo prefijo que emergencias móvil: ``/app/cliente/emergencias``.

Pruebas sugeridas (pytest + httpx AsyncClient):
- 404 si ``solicitud_id`` no es del cliente.
- 409 si la solicitud no está en estado pagable (p. ej. REGISTRADA).
- 409 si ya existe un pago PAGADO para la solicitud.
- 201/200 al crear pago con ``PAGO_SIMULADO_AUTOCOMPLETE=true`` (estado PAGADO + ``referencia_externa``).
- Con ``PAGO_SIMULADO_AUTOCOMPLETE=false``: POST crea PENDIENTE; POST completar pasa a PAGADO.
- 422 monto negativo o moneda inválida.
- Concurrencia: dos POST simultáneos → uno 409 por índice único parcial.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_permisos, require_permission
from app.modules.clientes_y_vehiculos.clientes.service import get_cliente_row_for_usuario, require_cliente_rol
from app.modules.pagos_y_comisiones.pagos import service
from app.modules.pagos_y_comisiones.pagos.schemas import PagoIniciadoRead, PagoRead, PagoSolicitudCreateIn, PagoStripeConfirmIn
from app.modules.acceso_y_administracion.usuarios.models import Usuario

emergencias_pagos_cliente_router = APIRouter(
    prefix="/app/cliente/emergencias",
    tags=["Pagos (cliente móvil)"],
)


async def _cliente_id(user: Usuario, db: AsyncSession) -> int:
    await require_cliente_rol(user.id, db)
    c = await get_cliente_row_for_usuario(user.id, db)
    return c.id


@emergencias_pagos_cliente_router.get(
    "/{solicitud_id}/pagos",
    response_model=list[PagoRead],
    dependencies=[Depends(require_permission("pagos:leer"))],
)
async def listar_pagos_de_solicitud(
    solicitud_id: int,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """Historial de intentos / pagos de una solicitud propia."""
    current_user, permisos = user_and_perms
    cid = await _cliente_id(current_user, db)
    return await service.listar_pagos_solicitud(
        current_user, cid, solicitud_id, db, permisos=permisos
    )


@emergencias_pagos_cliente_router.post(
    "/{solicitud_id}/pagos",
    response_model=PagoIniciadoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pagos:crear"))],
)
async def iniciar_pago_solicitud(
    solicitud_id: int,
    body: PagoSolicitudCreateIn,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra un cobro asociado a la solicitud.

    - Si ``STRIPE_SECRET_KEY`` está configurado: crea un **PaymentIntent** (pago **PENDIENTE**),
      devuelve ``stripe_client_secret`` y ``stripe_publishable_key`` para el PaymentSheet del móvil.
    - Si no: con ``PAGO_SIMULADO_AUTOCOMPLETE=true`` confirma al instante; si ``false``, queda **PENDIENTE**
      y ``POST .../pagos/{pago_id}/completar-simulado`` completa la simulación.
    """
    current_user, permisos = user_and_perms
    cid = await _cliente_id(current_user, db)
    return await service.crear_pago_solicitud(
        current_user, cid, solicitud_id, body, db, permisos=permisos
    )


@emergencias_pagos_cliente_router.post(
    "/{solicitud_id}/pagos/{pago_id}/confirmar-stripe",
    response_model=PagoRead,
    dependencies=[Depends(require_permission("pagos:crear"))],
)
async def confirmar_pago_stripe(
    solicitud_id: int,
    pago_id: int,
    body: PagoStripeConfirmIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tras éxito en Stripe SDK (PaymentSheet), sincroniza estado **PAGADO** consultando la API de Stripe."""
    cid = await _cliente_id(current_user, db)
    return await service.confirmar_pago_stripe(current_user, cid, solicitud_id, pago_id, body, db)


@emergencias_pagos_cliente_router.post(
    "/{solicitud_id}/pagos/{pago_id}/completar-simulado",
    response_model=PagoRead,
    dependencies=[Depends(require_permission("pagos:crear"))],
)
async def completar_pago_simulado(
    solicitud_id: int,
    pago_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirma un pago pendiente (integración simulada o paso 2 cuando la pasarela real confirme async)."""
    cid = await _cliente_id(current_user, db)
    return await service.completar_pago_simulado(current_user, cid, solicitud_id, pago_id, db)
