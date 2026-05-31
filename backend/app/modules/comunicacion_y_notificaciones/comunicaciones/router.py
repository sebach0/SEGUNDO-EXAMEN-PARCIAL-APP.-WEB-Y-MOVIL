# REST — orquesta APIs de notificaciones, FCM y mensajes por solicitud (CU19, CU21).
# La lógica vive en módulos: notificaciones, dispositivos_push, mensajes_solicitud.
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.comunicacion_y_notificaciones.dispositivos_push import service as fcm_service
from app.modules.comunicacion_y_notificaciones.dispositivos_push.schemas import FcmTokenRegisterIn
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud import service as msg_service
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.schemas import MensajeSolicitudCreateIn, MensajeSolicitudRead
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notif_service
from app.modules.comunicacion_y_notificaciones.notificaciones.schemas import NotificacionRead
from app.modules.clientes_y_vehiculos.clientes.service import require_cliente_rol
from app.modules.talleres_y_tecnicos.tecnico.service import require_tecnico_rol
from app.modules.acceso_y_administracion.usuarios.models import Usuario


async def _ensure_cliente(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    await require_cliente_rol(current_user.id, db)
    return current_user


async def _ensure_tecnico(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    await require_tecnico_rol(current_user.id, db)
    return current_user


cliente_router = APIRouter(prefix="/app/cliente", tags=["Comunicaciones (cliente)"])

emergencias_mensajes_cliente_router = APIRouter(
    prefix="/app/cliente/emergencias",
    tags=["Mensajes solicitud (cliente)"],
)

tecnico_router = APIRouter(prefix="/app/tecnico", tags=["Comunicaciones (técnico)"])


@cliente_router.post(
    "/dispositivos/fcm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("dispositivos:fcm"))],
)
async def cliente_registrar_fcm(
    body: FcmTokenRegisterIn,
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
):
    await fcm_service.registrar_fcm_token(current_user, body, db)


@cliente_router.delete(
    "/dispositivos/fcm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("dispositivos:fcm"))],
)
async def cliente_eliminar_fcm(
    body: FcmTokenRegisterIn,
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
):
    await fcm_service.eliminar_fcm_token(current_user, body, db)


@cliente_router.get(
    "/notificaciones",
    response_model=list[NotificacionRead],
    dependencies=[Depends(require_permission("notificaciones:leer"))],
)
async def cliente_listar_notificaciones(
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
    no_leidas: bool = Query(False),
    limit: int = Query(100, ge=1, le=200),
):
    return await notif_service.listar_notificaciones(
        current_user, db, solo_no_leidas=no_leidas, limit=limit
    )


@cliente_router.patch(
    "/notificaciones/{notificacion_id}/leida",
    response_model=NotificacionRead,
    dependencies=[Depends(require_permission("notificaciones:leer"))],
)
async def cliente_marcar_leida(
    notificacion_id: int,
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
):
    return await notif_service.marcar_notificacion_leida(current_user, notificacion_id, db)


@emergencias_mensajes_cliente_router.get(
    "/{solicitud_id}/mensajes",
    response_model=list[MensajeSolicitudRead],
    dependencies=[Depends(require_permission("mensajes:leer"))],
)
async def cliente_listar_mensajes(
    solicitud_id: int,
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
):
    return await msg_service.listar_mensajes(current_user, solicitud_id, db, actor="cliente")


@emergencias_mensajes_cliente_router.post(
    "/{solicitud_id}/mensajes",
    response_model=MensajeSolicitudRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("mensajes:crear"))],
)
async def cliente_enviar_mensaje(
    solicitud_id: int,
    body: MensajeSolicitudCreateIn,
    current_user: Usuario = Depends(_ensure_cliente),
    db: AsyncSession = Depends(get_db),
):
    return await msg_service.enviar_mensaje(current_user, solicitud_id, body, db, actor="cliente")


@tecnico_router.post(
    "/dispositivos/fcm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("dispositivos:fcm"))],
)
async def tecnico_registrar_fcm(
    body: FcmTokenRegisterIn,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    await fcm_service.registrar_fcm_token(current_user, body, db)


@tecnico_router.delete(
    "/dispositivos/fcm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("dispositivos:fcm"))],
)
async def tecnico_eliminar_fcm(
    body: FcmTokenRegisterIn,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    await fcm_service.eliminar_fcm_token(current_user, body, db)


@tecnico_router.get(
    "/notificaciones",
    response_model=list[NotificacionRead],
    dependencies=[Depends(require_permission("notificaciones:leer"))],
)
async def tecnico_listar_notificaciones(
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
    no_leidas: bool = Query(False),
    limit: int = Query(100, ge=1, le=200),
):
    return await notif_service.listar_notificaciones(
        current_user, db, solo_no_leidas=no_leidas, limit=limit
    )


@tecnico_router.patch(
    "/notificaciones/{notificacion_id}/leida",
    response_model=NotificacionRead,
    dependencies=[Depends(require_permission("notificaciones:leer"))],
)
async def tecnico_marcar_leida(
    notificacion_id: int,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    return await notif_service.marcar_notificacion_leida(current_user, notificacion_id, db)
