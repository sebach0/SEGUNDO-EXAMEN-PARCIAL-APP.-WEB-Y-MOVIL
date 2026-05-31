# Registro y baja de tokens FCM; disparo de pendientes y bienvenida en primer registro.
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.comunicacion_y_notificaciones.dispositivos_push import repository as fcm_repository
from app.modules.comunicacion_y_notificaciones.dispositivos_push.push_notify import send_fcm_to_usuario
from app.modules.comunicacion_y_notificaciones.dispositivos_push.schemas import FcmTokenRegisterIn
from app.modules.comunicacion_y_notificaciones.notificaciones import repository as notif_repository
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.clientes_y_vehiculos.clientes.service import require_cliente_rol


async def registrar_fcm_token(user, body: FcmTokenRegisterIn, db: AsyncSession) -> dict[str, str]:
    from app.modules.comunicacion_y_notificaciones.notificaciones.service import crear_notificacion_y_push

    now = utc_now_naive()
    tokens_previos = await fcm_repository.list_fcm_tokens_usuario(db, usuario_id=user.id)
    await fcm_repository.upsert_fcm_token(
        db,
        usuario_id=user.id,
        token=body.token.strip(),
        platform=body.platform.strip() if body.platform else None,
        now=now,
    )
    if not tokens_previos:
        pendientes = await notif_repository.list_notificaciones_usuario(
            db,
            usuario_id=user.id,
            solo_no_leidas=True,
            limit=10,
        )
        for n in reversed(pendientes):
            data = {
                "tipo": n.tipo.value,
                "notificacion_id": str(n.id),
                **({"solicitud_id": str(n.solicitud_id)} if n.solicitud_id is not None else {}),
            }
            await send_fcm_to_usuario(
                db,
                usuario_id=user.id,
                titulo=n.titulo,
                cuerpo=n.mensaje,
                data=data,
                log_omitir_si_sin_tokens=False,
            )
    if not tokens_previos:
        es_cliente = False
        try:
            await require_cliente_rol(user.id, db)
            es_cliente = True
        except HTTPException:
            es_cliente = False
        if es_cliente:
            await crear_notificacion_y_push(
                db,
                usuario_destino_id=user.id,
                solicitud_id=None,
                tipo=TipoNotificacionEnum.SOLICITUD_CREADA,
                titulo="Bienvenido a Emergencias Viales",
                mensaje="Tu cuenta está activa y las notificaciones push quedaron habilitadas en este dispositivo.",
            )
    await db.commit()
    return {"status": "ok"}


async def eliminar_fcm_token(user, body: FcmTokenRegisterIn, db: AsyncSession) -> dict[str, str]:
    n = await fcm_repository.delete_fcm_token(db, usuario_id=user.id, token=body.token.strip())
    await db.commit()
    return {"status": "ok", "eliminados": str(n)}
