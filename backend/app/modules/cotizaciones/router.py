from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_permisos, require_permission
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.clientes_y_vehiculos.clientes.service import get_cliente_row_for_usuario, require_cliente_rol
from app.modules.cotizaciones import service
from app.modules.cotizaciones.schemas import (
    CotizacionContextoRead,
    CotizacionCreateIn,
    CotizacionRead,
    CotizacionRechazarIn,
    CotizacionRespondIn,
)
from app.modules.talleres_y_tecnicos.taller_responsable.router import require_taller_responsable
from app.modules.talleres_y_tecnicos.talleres.models import Taller

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"])


async def _cliente_id_or_none(user: Usuario, db: AsyncSession) -> int | None:
    res = await db.execute(select(Cliente.id).where(Cliente.usuario_id == user.id))
    return res.scalar_one_or_none()


async def _require_cliente_id(user: Usuario, db: AsyncSession) -> int:
    await require_cliente_rol(user.id, db)
    c = await get_cliente_row_for_usuario(user.id, db)
    return c.id


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=list[CotizacionRead],
    dependencies=[Depends(require_permission("cotizaciones:leer"))],
)
async def listar_cotizaciones(
    solicitud_id: int,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """Lista cotizaciones de una solicitud (admin, taller o cliente dueño)."""
    user, permisos = user_and_perms
    cliente_id = await _cliente_id_or_none(user, db)
    return await service.listar_cotizaciones(
        solicitud_id=solicitud_id,
        db=db,
        user=user,
        permisos=permisos,
        cliente_id=cliente_id,
    )


@router.get(
    "/solicitudes/{solicitud_id}/contexto-oferta",
    response_model=CotizacionContextoRead,
    dependencies=[Depends(require_permission("cotizaciones:crear"))],
)
async def contexto_oferta_cotizacion(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Distancia al incidente y servicios del taller para armar la oferta."""
    _, taller = ctx
    return await service.contexto_oferta_taller(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        db=db,
    )


@router.post(
    "/solicitudes/{solicitud_id}",
    response_model=CotizacionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("cotizaciones:crear"))],
)
async def proponer_cotizacion(
    solicitud_id: int,
    body: CotizacionCreateIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """El taller responsable envía una cotización para una solicitud de emergencia."""
    _, taller = ctx
    user, permisos = user_and_perms
    return await service.proponer_cotizacion(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        body=body,
        db=db,
        user=user,
        permisos=permisos,
    )


@router.post(
    "/solicitudes/{solicitud_id}/cotizacion/{cotizacion_id}/seleccionar",
    response_model=CotizacionRead,
    dependencies=[Depends(require_permission("cotizaciones:aceptar"))],
)
async def seleccionar_cotizacion(
    solicitud_id: int,
    cotizacion_id: int,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """El cliente selecciona una cotización; las demás pasan a EXPIRADA y el taller queda asignado."""
    user, permisos = user_and_perms
    cliente_id = await _require_cliente_id(user, db)
    return await service.seleccionar_cotizacion(
        solicitud_id=solicitud_id,
        cotizacion_id=cotizacion_id,
        db=db,
        user=user,
        permisos=permisos,
        cliente_id=cliente_id,
    )


@router.patch(
    "/solicitudes/{solicitud_id}/cotizacion/{cotizacion_id}/rechazar",
    response_model=CotizacionRead,
    dependencies=[Depends(require_permission("cotizaciones:rechazar"))],
)
async def rechazar_cotizacion(
    solicitud_id: int,
    cotizacion_id: int,
    body: CotizacionRechazarIn | None = None,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """CU48 — el cliente rechaza una cotización ENVIADA."""
    user, permisos = user_and_perms
    cliente_id = await _require_cliente_id(user, db)
    return await service.rechazar_cotizacion(
        solicitud_id=solicitud_id,
        cotizacion_id=cotizacion_id,
        db=db,
        user=user,
        permisos=permisos,
        cliente_id=cliente_id,
        comment=body.comment if body else None,
    )


@router.patch(
    "/solicitudes/{solicitud_id}/cotizacion/{cotizacion_id}/respond",
    response_model=CotizacionRead,
    dependencies=[Depends(require_permission("cotizaciones:aceptar"))],
)
async def responder_cotizacion(
    solicitud_id: int,
    cotizacion_id: int,
    body: CotizacionRespondIn,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """CU48 — aprobar (ACEPTADA) o rechazar (RECHAZADA) en un solo endpoint."""
    user, permisos = user_and_perms
    cliente_id = await _require_cliente_id(user, db)
    return await service.responder_cotizacion(
        solicitud_id=solicitud_id,
        cotizacion_id=cotizacion_id,
        body=body,
        db=db,
        user=user,
        permisos=permisos,
        cliente_id=cliente_id,
    )
