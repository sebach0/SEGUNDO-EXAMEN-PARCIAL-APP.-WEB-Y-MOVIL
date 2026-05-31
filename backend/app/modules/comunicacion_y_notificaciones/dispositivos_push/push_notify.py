# Envío FCM a un usuario: un solo lugar para listar tokens y disparar el cliente síncrono en hilo.
from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.comunicacion_y_notificaciones.dispositivos_push import fcm_client
from app.modules.comunicacion_y_notificaciones.dispositivos_push import repository as fcm_repository

_log = logging.getLogger(__name__)


async def send_fcm_to_usuario(
    db: AsyncSession,
    *,
    usuario_id: int,
    titulo: str,
    cuerpo: str,
    data: dict[str, str],
    log_omitir_si_sin_tokens: bool = False,
) -> None:
    """
    Resuelve tokens FCM del usuario y envía multicast. Si FCM está deshabilitado o
    no hay tokens, no hace nada. ``log_omitir_si_sin_tokens`` controla un log informativo
    cuando no hay dispositivos (p. ej. notificación nueva vs. re-envío al registrar token).
    """
    if not settings.FCM_ENABLED:
        return
    tokens = await fcm_repository.list_fcm_tokens_usuario(db, usuario_id=usuario_id)
    if not tokens:
        if log_omitir_si_sin_tokens:
            _log.info(
                "FCM omitido: usuario_id=%s sin tokens registrados (titulo=%r)",
                usuario_id,
                titulo,
            )
        return
    try:
        await asyncio.to_thread(
            fcm_client.send_push_multicast_sync,
            tokens,
            title=titulo,
            body=cuerpo,
            data=data,
        )
    except Exception:
        _log.exception("Error en hilo FCM")
