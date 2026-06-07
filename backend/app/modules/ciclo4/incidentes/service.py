# Servicio — Ciclo 4: Incidentes v2
# Cubre: CU36, CU37 (cambio de estado + historial + WS + evento).
# =========================================================
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.ciclo4.incidentes.models import (
    EstadoIncidenteEnum,
    EventoTiempoReal,
    Incidente,
    IncidenteEstadoHistorial,
    IncidenteTracking,
    OrigenIncidenteEnum,
    SyncEstadoEnum,
)
from app.modules.ciclo4.incidentes.schemas import (
    CambiarEstadoIn,
    IncidenteCreateIn,
    TrackingCreateIn,
)
from app.modules.ciclo4.websocket.manager import manager as ws_manager


# ── Helpers ──────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _map_estado_timestamp(inc: Incidente, nuevo_estado: EstadoIncidenteEnum) -> None:
    """Actualiza el timestamp correspondiente al nuevo estado."""
    now = _utcnow()
    mapping = {
        EstadoIncidenteEnum.BUSCANDO_TALLER: "buscando_taller_en",
        EstadoIncidenteEnum.TALLER_ASIGNADO: "asignado_en",
        EstadoIncidenteEnum.EN_CAMINO:       "en_camino_en",
        EstadoIncidenteEnum.EN_ATENCION:     "en_atencion_en",
        EstadoIncidenteEnum.FINALIZADO:      "finalizado_en",
        EstadoIncidenteEnum.CANCELADO:       "cancelado_en",
    }
    campo = mapping.get(nuevo_estado)
    if campo:
        setattr(inc, campo, now)


_TIPO_EVENTO_POR_ESTADO = {
    EstadoIncidenteEnum.BUSCANDO_TALLER: "ESTADO_CAMBIADO",
    EstadoIncidenteEnum.TALLER_ASIGNADO: "TALLER_ACEPTO",
    EstadoIncidenteEnum.EN_CAMINO:       "AUXILIO_EN_CAMINO",
    EstadoIncidenteEnum.EN_ATENCION:     "SERVICIO_ATENDIDO",
    EstadoIncidenteEnum.FINALIZADO:      "SERVICIO_FINALIZADO",
    EstadoIncidenteEnum.CANCELADO:       "ESTADO_CAMBIADO",
    EstadoIncidenteEnum.PENDIENTE:       "ESTADO_CAMBIADO",
}

_MENSAJE_POR_ESTADO = {
    EstadoIncidenteEnum.BUSCANDO_TALLER: "Buscando taller disponible",
    EstadoIncidenteEnum.TALLER_ASIGNADO: "Se asignó un taller",
    EstadoIncidenteEnum.EN_CAMINO:       "El auxilio está en camino",
    EstadoIncidenteEnum.EN_ATENCION:     "El técnico está atendiendo el incidente",
    EstadoIncidenteEnum.FINALIZADO:      "Servicio finalizado",
    EstadoIncidenteEnum.CANCELADO:       "Incidente cancelado",
    EstadoIncidenteEnum.PENDIENTE:       "Incidente registrado",
}


# ── Lookup con tenant check ───────────────────────────────────────────────────

async def _get_incidente_o_404(
    incidente_id: int, tenant_id: int, db: AsyncSession
) -> Incidente:
    """
    Retorna el incidente si pertenece al tenant.
    Lanza 404 si no existe o pertenece a otro tenant (opaco intencionalmente).
    """
    result = await db.execute(
        select(Incidente)
        .options(
            selectinload(Incidente.historial_estados),
            selectinload(Incidente.tracking_records),
            selectinload(Incidente.eventos),
        )
        .where(Incidente.id == incidente_id, Incidente.tenant_id == tenant_id)
    )
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado",
        )
    return inc


async def _get_cliente_id_para_usuario(usuario_id: int, db: AsyncSession) -> int:
    """Obtiene el cliente_id del usuario autenticado."""
    result = await db.execute(
        select(Cliente).where(Cliente.usuario_id == usuario_id)
    )
    cliente = result.scalar_one_or_none()
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene perfil de cliente",
        )
    return cliente.id


# ── Crear incidente ───────────────────────────────────────────────────────────

async def crear_incidente(
    body: IncidenteCreateIn,
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
) -> Incidente:
    """
    CU11 (Ciclo 4 version): Crea un incidente en línea.
    Para OFFLINE usa POST /api/sync/incidents.
    Valida que el usuario tenga perfil de cliente.
    """
    cliente_id = await _get_cliente_id_para_usuario(usuario_id, db)
    now = _utcnow()

    inc = Incidente(
        tenant_id=tenant_id,
        cliente_id=cliente_id,
        vehiculo_id=body.vehiculo_id,
        tipo_incidente_id=body.tipo_incidente_id,
        zona_id=body.zona_id,
        descripcion=body.descripcion,
        prioridad=body.prioridad,
        latitud=body.latitud,
        longitud=body.longitud,
        direccion_referencia=body.direccion_referencia,
        sla_minutos=body.sla_minutos,
        origen=body.origen,
        client_uuid=body.client_uuid,
        sync_estado=SyncEstadoEnum.SINCRONIZADO,
        estado=EstadoIncidenteEnum.PENDIENTE,
        reportado_en=now,
        creado_en=now,
        actualizado_en=now,
    )
    db.add(inc)
    await db.flush()  # obtiene el id antes del commit

    # Primer registro en historial
    historial = IncidenteEstadoHistorial(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        estado_anterior=None,
        estado_nuevo=EstadoIncidenteEnum.PENDIENTE.value,
        usuario_id=usuario_id,
        comentario="Incidente creado",
        creado_en=now,
    )
    db.add(historial)

    # Primer evento de tiempo real
    evento = EventoTiempoReal(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        usuario_id=usuario_id,
        canal=f"incidente:{inc.id}",
        tipo_evento="ESTADO_CAMBIADO",
        payload={"estado": "PENDIENTE", "mensaje": "Incidente creado"},
        emitido_en=now,
    )
    db.add(evento)
    await db.flush()
    return inc


# ── Cambiar estado (CU37) ─────────────────────────────────────────────────────

async def cambiar_estado(
    incidente_id: int,
    body: CambiarEstadoIn,
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
) -> Incidente:
    """
    CU37: Cambia el estado del incidente.
    1. Valida acceso por tenant.
    2. Actualiza estado + timestamp correspondiente.
    3. Guarda IncidenteEstadoHistorial (auditoría).
    4. Crea EventoTiempoReal (log persistente).
    5. Emite por WebSocket a todos los conectados al incidente.
    """
    inc = await _get_incidente_o_404(incidente_id, tenant_id, db)
    now = _utcnow()

    estado_anterior = inc.estado.value
    inc.estado = body.nuevo_estado
    inc.actualizado_en = now

    # Timestamp específico del estado
    _map_estado_timestamp(inc, body.nuevo_estado)

    if body.nuevo_estado == EstadoIncidenteEnum.CANCELADO and body.motivo_cancelacion:
        inc.motivo_cancelacion = body.motivo_cancelacion

    # Historial
    historial = IncidenteEstadoHistorial(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        estado_anterior=estado_anterior,
        estado_nuevo=body.nuevo_estado.value,
        usuario_id=usuario_id,
        comentario=body.comentario,
        creado_en=now,
    )
    db.add(historial)

    # Tipo de evento y mensaje según el nuevo estado
    tipo_evento = _TIPO_EVENTO_POR_ESTADO.get(body.nuevo_estado, "ESTADO_CAMBIADO")
    mensaje = _MENSAJE_POR_ESTADO.get(body.nuevo_estado, "Estado actualizado")

    evento = EventoTiempoReal(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        usuario_id=usuario_id,
        canal=f"incidente:{inc.id}",
        tipo_evento=tipo_evento,
        payload={
            "estado_anterior": estado_anterior,
            "estado_nuevo": body.nuevo_estado.value,
            "comentario": body.comentario,
        },
        emitido_en=now,
    )
    db.add(evento)
    await db.flush()

    # WebSocket — no bloquea si nadie está conectado
    await ws_manager.broadcast_to_incident(
        incident_id=inc.id,
        event_type=tipo_evento,
        status=body.nuevo_estado.value,
        message=mensaje,
        payload={
            "estado_anterior": estado_anterior,
            "comentario": body.comentario,
        },
    )

    return inc


# ── Agregar punto GPS (CU36/CU37 — tracking en tiempo real) ──────────────────

async def agregar_tracking(
    incidente_id: int,
    body: TrackingCreateIn,
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
) -> IncidenteTracking:
    """
    POST /api/incidents/{id}/tracking
    Guarda un punto GPS y emite TRACKING_UPDATE por WebSocket.
    """
    # Solo verificamos pertenencia al tenant (no cargamos relaciones pesadas)
    result = await db.execute(
        select(Incidente).where(
            Incidente.id == incidente_id, Incidente.tenant_id == tenant_id
        )
    )
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    now = _utcnow()
    punto = IncidenteTracking(
        tenant_id=tenant_id,
        incidente_id=incidente_id,
        latitud=body.latitud,
        longitud=body.longitud,
        velocidad_kmh=body.velocidad_kmh,
        registrado_en=now,
    )
    db.add(punto)

    evento = EventoTiempoReal(
        tenant_id=tenant_id,
        incidente_id=incidente_id,
        usuario_id=usuario_id,
        canal=f"incidente:{incidente_id}",
        tipo_evento="TRACKING_UPDATE",
        payload={
            "lat": float(body.latitud),
            "lng": float(body.longitud),
            "velocidad_kmh": float(body.velocidad_kmh) if body.velocidad_kmh else None,
        },
        emitido_en=now,
    )
    db.add(evento)
    await db.flush()

    # Emitir por WebSocket
    await ws_manager.broadcast_to_incident(
        incident_id=incidente_id,
        event_type="TRACKING_UPDATE",
        status=inc.estado.value,
        message="Posición GPS actualizada",
        payload={
            "lat": float(body.latitud),
            "lng": float(body.longitud),
            "velocidad_kmh": float(body.velocidad_kmh) if body.velocidad_kmh else None,
        },
    )

    return punto


# ── Obtener tracking reciente ─────────────────────────────────────────────────

async def get_tracking(
    incidente_id: int, tenant_id: int, db: AsyncSession, limit: int = 50
) -> list[IncidenteTracking]:
    """
    GET /api/incidents/{id}/tracking
    CU36: el cliente consulta los últimos N puntos GPS del técnico.
    """
    result = await db.execute(
        select(IncidenteTracking)
        .where(
            IncidenteTracking.incidente_id == incidente_id,
            IncidenteTracking.tenant_id == tenant_id,
        )
        .order_by(IncidenteTracking.registrado_en.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Obtener detalle ───────────────────────────────────────────────────────────

async def get_incidente_detalle(
    incidente_id: int, tenant_id: int, db: AsyncSession
) -> Incidente:
    """GET /api/incidents/{id} — con historial + tracking + eventos recientes."""
    return await _get_incidente_o_404(incidente_id, tenant_id, db)


# ── Listar incidentes del usuario ─────────────────────────────────────────────

async def listar_incidentes_usuario(
    usuario_id: int, tenant_id: int, db: AsyncSession, limit: int = 50
) -> list[Incidente]:
    cliente_id = await _get_cliente_id_para_usuario(usuario_id, db)
    result = await db.execute(
        select(Incidente)
        .where(Incidente.cliente_id == cliente_id, Incidente.tenant_id == tenant_id)
        .order_by(Incidente.creado_en.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
