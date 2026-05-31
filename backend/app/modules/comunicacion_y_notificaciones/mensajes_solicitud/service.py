# Chat por solicitud de emergencia (cliente ↔ técnico asignado).
from __future__ import annotations

from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud import repository as msg_repository
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.schemas import MensajeSolicitudCreateIn, MensajeSolicitudRead
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.comunicacion_y_notificaciones.notificaciones.service import crear_notificacion_y_push
from app.modules.clientes_y_vehiculos.clientes.service import get_cliente_row_for_usuario, require_cliente_rol
from app.modules.talleres_y_tecnicos.tecnico.service import get_tecnico_row_for_usuario, require_tecnico_rol
from app.modules.acceso_y_administracion.usuarios.models import Usuario


async def _get_solicitud_or_404(db: AsyncSession, solicitud_id: int) -> SolicitudEmergencia:
    sol = await msg_repository.get_solicitud_by_id(db, solicitud_id)
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return sol


async def _assert_cliente_solicitud_propia(
    db: AsyncSession, user: Usuario, sol: SolicitudEmergencia
) -> None:
    await require_cliente_rol(user.id, db)
    c = await get_cliente_row_for_usuario(user.id, db)
    if sol.cliente_id != c.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")


async def _assert_tecnico_asignado(
    db: AsyncSession, user: Usuario, sol: SolicitudEmergencia
) -> None:
    await require_tecnico_rol(user.id, db)
    t = await get_tecnico_row_for_usuario(user.id, db)
    if sol.tecnico_id is None or sol.tecnico_id != t.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No estás asignado a esta solicitud.",
        )


async def listar_mensajes(
    user: Usuario,
    solicitud_id: int,
    db: AsyncSession,
    actor: Literal["cliente", "tecnico"],
) -> list[MensajeSolicitudRead]:
    sol = await _get_solicitud_or_404(db, solicitud_id)
    if actor == "cliente":
        await _assert_cliente_solicitud_propia(db, user, sol)
    else:
        await _assert_tecnico_asignado(db, user, sol)
    rows = await msg_repository.list_mensajes_solicitud(db, solicitud_id=solicitud_id)
    return [MensajeSolicitudRead.model_validate(x) for x in rows]


async def enviar_mensaje(
    user: Usuario,
    solicitud_id: int,
    body: MensajeSolicitudCreateIn,
    db: AsyncSession,
    actor: Literal["cliente", "tecnico"],
) -> MensajeSolicitudRead:
    sol = await _get_solicitud_or_404(db, solicitud_id)
    texto = body.mensaje.strip()
    now = utc_now_naive()

    if actor == "cliente":
        await _assert_cliente_solicitud_propia(db, user, sol)
        if sol.tecnico_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Aún no hay técnico asignado; no se puede enviar mensaje.",
            )
        tu = await msg_repository.get_tecnico_usuario_id_for_solicitud(
            db, tecnico_row_id=sol.tecnico_id
        )
        if tu is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Técnico inválido."
            )
        cu = await msg_repository.get_cliente_usuario_id(db, cliente_id=sol.cliente_id)
        if cu is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cliente inválido."
            )
        if user.id != cu:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Solo el cliente titular puede escribir."
            )
        emisor, receptor = user.id, tu
    else:
        await _assert_tecnico_asignado(db, user, sol)
        cu = await msg_repository.get_cliente_usuario_id(db, cliente_id=sol.cliente_id)
        if cu is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cliente inválido."
            )
        emisor, receptor = user.id, cu

    msg = await msg_repository.insert_mensaje(
        db,
        solicitud_id=solicitud_id,
        emisor_usuario_id=emisor,
        receptor_usuario_id=receptor,
        texto=texto,
        created_at=now,
    )
    await db.flush()

    await crear_notificacion_y_push(
        db,
        usuario_destino_id=receptor,
        solicitud_id=solicitud_id,
        tipo=TipoNotificacionEnum.MENSAJE_NUEVO,
        titulo="Nuevo mensaje",
        mensaje=texto[:120] + ("…" if len(texto) > 120 else ""),
    )
    await db.commit()
    await db.refresh(msg)
    return MensajeSolicitudRead.model_validate(msg)
