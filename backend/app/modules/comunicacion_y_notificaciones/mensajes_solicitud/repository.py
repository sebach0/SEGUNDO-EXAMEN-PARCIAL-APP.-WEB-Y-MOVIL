from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.models import SolicitudMensaje
from app.modules.talleres_y_tecnicos.talleres.models import Tecnico
from app.modules.clientes_y_vehiculos.clientes.models import Cliente


async def get_solicitud_by_id(db: AsyncSession, solicitud_id: int) -> SolicitudEmergencia | None:
    r = await db.execute(select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id))
    return r.scalar_one_or_none()


async def get_cliente_usuario_id(db: AsyncSession, *, cliente_id: int) -> int | None:
    r = await db.execute(select(Cliente.usuario_id).where(Cliente.id == cliente_id))
    row = r.scalar_one_or_none()
    return int(row) if row is not None else None


async def get_tecnico_usuario_id_for_solicitud(db: AsyncSession, *, tecnico_row_id: int) -> int | None:
    r = await db.execute(select(Tecnico.usuario_id).where(Tecnico.id == tecnico_row_id))
    row = r.scalar_one_or_none()
    return int(row) if row is not None else None


async def get_tecnico_id_for_usuario(db: AsyncSession, *, usuario_id: int) -> int | None:
    r = await db.execute(select(Tecnico.id).where(Tecnico.usuario_id == usuario_id))
    row = r.scalar_one_or_none()
    return int(row) if row is not None else None


async def list_mensajes_solicitud(db: AsyncSession, *, solicitud_id: int) -> list[SolicitudMensaje]:
    r = await db.execute(
        select(SolicitudMensaje)
        .where(SolicitudMensaje.solicitud_id == solicitud_id)
        .order_by(SolicitudMensaje.created_at.asc())
    )
    return list(r.scalars().all())


async def insert_mensaje(
    db: AsyncSession,
    *,
    solicitud_id: int,
    emisor_usuario_id: int,
    receptor_usuario_id: int,
    texto: str,
    created_at,
) -> SolicitudMensaje:
    row = SolicitudMensaje(
        solicitud_id=solicitud_id,
        emisor_usuario_id=emisor_usuario_id,
        receptor_usuario_id=receptor_usuario_id,
        mensaje=texto,
        created_at=created_at,
        leido_at=None,
    )
    db.add(row)
    await db.flush()
    return row
