# Notificaciones in-app y disparo de push (FCM) asociado.
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.comunicacion_y_notificaciones.dispositivos_push.push_notify import send_fcm_to_usuario
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.comunicacion_y_notificaciones.notificaciones import repository as notif_repository
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.comunicacion_y_notificaciones.notificaciones.schemas import NotificacionRead
from app.modules.talleres_y_tecnicos.talleres.models import Tecnico
from app.modules.clientes_y_vehiculos.clientes.models import Cliente


async def crear_notificacion_y_push(
    db: AsyncSession,
    *,
    usuario_destino_id: int,
    solicitud_id: int | None,
    tipo: TipoNotificacionEnum,
    titulo: str,
    mensaje: str,
    extra_data: dict[str, str] | None = None,
) -> NotificacionRead:
    now = utc_now_naive()
    row = await notif_repository.insert_notificacion(
        db,
        usuario_id=usuario_destino_id,
        solicitud_id=solicitud_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        created_at=now,
    )
    data: dict[str, str] = {
        "tipo": tipo.value,
        "notificacion_id": str(row.id),
        **({"solicitud_id": str(solicitud_id)} if solicitud_id is not None else {}),
        **(extra_data or {}),
    }
    await send_fcm_to_usuario(
        db,
        usuario_id=usuario_destino_id,
        titulo=titulo,
        cuerpo=mensaje,
        data=data,
        log_omitir_si_sin_tokens=True,
    )
    return NotificacionRead.model_validate(row)


async def notificar_cliente_solicitud_emergencia(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    tipo: TipoNotificacionEnum,
    titulo: str,
    mensaje: str,
    extra_data: dict[str, str] | None = None,
) -> None:
    res = await db.execute(select(Cliente).where(Cliente.id == solicitud.cliente_id))
    cli = res.scalar_one_or_none()
    if cli is None:
        return
    await crear_notificacion_y_push(
        db,
        usuario_destino_id=cli.usuario_id,
        solicitud_id=solicitud.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        extra_data=extra_data,
    )


async def notificar_tecnico_solicitud_emergencia(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    tipo: TipoNotificacionEnum,
    titulo: str,
    mensaje: str,
) -> None:
    if solicitud.tecnico_id is None:
        return
    res = await db.execute(select(Tecnico).where(Tecnico.id == solicitud.tecnico_id))
    tec = res.scalar_one_or_none()
    if tec is None:
        return
    await crear_notificacion_y_push(
        db,
        usuario_destino_id=tec.usuario_id,
        solicitud_id=solicitud.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


async def notificar_taller_responsable_solicitud(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    tipo: TipoNotificacionEnum,
    titulo: str,
    mensaje: str,
) -> None:
    if solicitud.taller_id is None:
        return
    from app.modules.talleres_y_tecnicos.talleres.models import Taller

    res = await db.execute(select(Taller).where(Taller.id == solicitud.taller_id))
    taller = res.scalar_one_or_none()
    if taller is None:
        return
    await crear_notificacion_y_push(
        db,
        usuario_destino_id=taller.usuario_responsable_id,
        solicitud_id=solicitud.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


async def listar_notificaciones(
    user, db: AsyncSession, *, solo_no_leidas: bool, limit: int
) -> list[NotificacionRead]:
    rows = await notif_repository.list_notificaciones_usuario(
        db, usuario_id=user.id, solo_no_leidas=solo_no_leidas, limit=limit
    )
    return [NotificacionRead.model_validate(x) for x in rows]


async def marcar_notificacion_leida(user, notif_id: int, db: AsyncSession) -> NotificacionRead:
    n = await notif_repository.get_notificacion_propia(db, notif_id=notif_id, usuario_id=user.id)
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    await notif_repository.marcar_notificacion_leida(db, n=n, leida_at=utc_now_naive())
    await db.commit()
    await db.refresh(n)
    return NotificacionRead.model_validate(n)
