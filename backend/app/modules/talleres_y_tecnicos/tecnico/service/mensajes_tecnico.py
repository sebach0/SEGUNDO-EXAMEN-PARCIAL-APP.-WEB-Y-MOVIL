from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comunicacion_y_notificaciones.mensajes_solicitud import service as mensajes_service
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.schemas import MensajeSolicitudCreateIn, MensajeSolicitudRead
from app.modules.acceso_y_administracion.usuarios.models import Usuario


async def listar_mensajes_solicitud(
    user: Usuario, solicitud_id: int, db: AsyncSession
) -> list[MensajeSolicitudRead]:
    return await mensajes_service.listar_mensajes(user, solicitud_id, db, actor="tecnico")


async def enviar_mensaje_solicitud(
    user: Usuario, solicitud_id: int, body: MensajeSolicitudCreateIn, db: AsyncSession
) -> MensajeSolicitudRead:
    return await mensajes_service.enviar_mensaje(user, solicitud_id, body, db, actor="tecnico")
