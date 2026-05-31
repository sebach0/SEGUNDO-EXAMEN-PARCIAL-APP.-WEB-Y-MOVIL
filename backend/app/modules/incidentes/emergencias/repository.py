# Acceso a datos — emergencias (sin reglas de negocio)
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
    SolicitudEvidencia,
    SolicitudHistorialEstado,
    SolicitudUbicacion,
)
from app.modules.talleres_y_tecnicos.talleres.models import Tecnico
from app.modules.clientes_y_vehiculos.vehiculos.models import Vehiculo


async def get_vehiculo_if_cliente(
    db: AsyncSession, *, vehiculo_id: int, cliente_id: int
) -> Vehiculo | None:
    r = await db.execute(
        select(Vehiculo).where(
            Vehiculo.id == vehiculo_id,
            Vehiculo.cliente_id == cliente_id,
        )
    )
    return r.scalar_one_or_none()


async def insert_solicitud(
    db: AsyncSession,
    *,
    cliente_id: int,
    vehiculo_id: int,
    descripcion_texto: str | None,
    estado: EstadoSolicitudSeguimientoEnum,
    created_at,
    updated_at,
) -> SolicitudEmergencia:
    row = SolicitudEmergencia(
        cliente_id=cliente_id,
        vehiculo_id=vehiculo_id,
        descripcion_texto=descripcion_texto,
        estado=estado,
        created_at=created_at,
        updated_at=updated_at,
    )
    db.add(row)
    await db.flush()
    return row


async def insert_historial_estado(
    db: AsyncSession,
    *,
    solicitud_id: int,
    estado_anterior: EstadoSolicitudSeguimientoEnum | None,
    estado_nuevo: EstadoSolicitudSeguimientoEnum,
    usuario_id: int | None,
    observacion: str | None,
    created_at,
) -> SolicitudHistorialEstado:
    row = SolicitudHistorialEstado(
        solicitud_id=solicitud_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario_id=usuario_id,
        observacion=observacion,
        created_at=created_at,
    )
    db.add(row)
    await db.flush()
    return row


async def get_solicitud_for_cliente(
    db: AsyncSession, *, solicitud_id: int, cliente_id: int, with_children: bool = False
) -> SolicitudEmergencia | None:
    stmt = select(SolicitudEmergencia).where(
        SolicitudEmergencia.id == solicitud_id,
        SolicitudEmergencia.cliente_id == cliente_id,
    )
    if with_children:
        stmt = stmt.options(
            selectinload(SolicitudEmergencia.ubicaciones),
            selectinload(SolicitudEmergencia.evidencias),
        )
    r = await db.execute(stmt)
    return r.scalar_one_or_none()


async def get_solicitud_seguimiento_for_cliente(
    db: AsyncSession, *, solicitud_id: int, cliente_id: int
) -> SolicitudEmergencia | None:
    stmt = (
        select(SolicitudEmergencia)
        .where(
            SolicitudEmergencia.id == solicitud_id,
            SolicitudEmergencia.cliente_id == cliente_id,
        )
        .options(
            selectinload(SolicitudEmergencia.historial_estados),
            selectinload(SolicitudEmergencia.ubicaciones),
            selectinload(SolicitudEmergencia.evidencias),
            joinedload(SolicitudEmergencia.taller),
            joinedload(SolicitudEmergencia.tecnico).joinedload(Tecnico.usuario),
        )
    )
    r = await db.execute(stmt)
    return r.unique().scalar_one_or_none()


async def list_solicitudes_cliente(
    db: AsyncSession, *, cliente_id: int, limit: int = 100
) -> list[SolicitudEmergencia]:
    r = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.cliente_id == cliente_id)
        .order_by(SolicitudEmergencia.created_at.desc())
        .limit(limit)
    )
    return list(r.scalars().all())


async def clear_ubicacion_actual_for_solicitud(db: AsyncSession, solicitud_id: int) -> None:
    await db.execute(
        update(SolicitudUbicacion)
        .where(
            SolicitudUbicacion.solicitud_id == solicitud_id,
            SolicitudUbicacion.es_actual.is_(True),
        )
        .values(es_actual=False)
    )


async def insert_ubicacion(
    db: AsyncSession,
    *,
    solicitud_id: int,
    latitud,
    longitud,
    precision_metros,
    direccion_referencia: str | None,
    es_actual: bool,
    registrado_at,
) -> SolicitudUbicacion:
    row = SolicitudUbicacion(
        solicitud_id=solicitud_id,
        latitud=latitud,
        longitud=longitud,
        precision_metros=precision_metros,
        direccion_referencia=direccion_referencia,
        es_actual=es_actual,
        registrado_at=registrado_at,
    )
    db.add(row)
    await db.flush()
    return row


async def update_solicitud_ai_payload(
    db: AsyncSession,
    *,
    solicitud_id: int,
    payload: dict,
    updated_at,
) -> None:
    await db.execute(
        update(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .values(ai_payload=payload, updated_at=updated_at)
    )


async def update_tecnico_ultima_ubicacion(
    db: AsyncSession,
    *,
    solicitud_id: int,
    latitud,
    longitud,
    precision_metros,
    ubicacion_at,
) -> None:
    await db.execute(
        update(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .values(
            tecnico_ult_latitud=latitud,
            tecnico_ult_longitud=longitud,
            tecnico_ult_precision_metros=precision_metros,
            tecnico_ult_ubicacion_at=ubicacion_at,
            updated_at=ubicacion_at,
        )
    )


async def insert_evidencia(
    db: AsyncSession,
    *,
    solicitud_id: int,
    tipo,
    archivo_url: str,
    mime_type: str | None,
    nombre_archivo: str | None,
    tamano_bytes: int | None,
    created_at,
) -> SolicitudEvidencia:
    row = SolicitudEvidencia(
        solicitud_id=solicitud_id,
        tipo=tipo,
        archivo_url=archivo_url,
        mime_type=mime_type,
        nombre_archivo=nombre_archivo,
        tamano_bytes=tamano_bytes,
        created_at=created_at,
    )
    db.add(row)
    await db.flush()
    return row
