# Servicio — Ciclo 4: Sincronización Offline (CU38-CU42)
# =========================================================
# CU39: Sincronizar emergencia pendiente (móvil → backend)
# CU40: Consultar estado de sincronización
# CU41: Registrar evento offline web
# CU42: Sincronizar eventos pendientes web
# =========================================================
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.ciclo4.incidentes.models import (
    EstadoIncidenteEnum,
    EventoTiempoReal,
    Incidente,
    IncidenteEstadoHistorial,
    OrigenIncidenteEnum,
    SyncEstadoEnum,
)
from app.modules.ciclo4.sync.models import (
    ErrorSincronizacion,
    SincronizacionOffline,
)
from app.modules.ciclo4.sync.schemas import (
    SyncIncidenteIn,
    SyncIncidenteResultado,
    WebEventoIn,
    WebEventoResultado,
    WebSyncResultado,
)
from app.modules.ciclo4.websocket.manager import manager as ws_manager


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_cliente_o_403(usuario_id: int, db: AsyncSession) -> Cliente:
    result = await db.execute(
        select(Cliente).where(Cliente.usuario_id == usuario_id)
    )
    c = result.scalar_one_or_none()
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene perfil de cliente",
        )
    return c


# ── CU39 — Sincronizar incidente offline móvil ────────────────────────────────

async def sincronizar_incidente_movil(
    body: SyncIncidenteIn,
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
) -> SyncIncidenteResultado:
    """
    Anti-duplicado:
      1. Busca por (tenant_id, client_uuid) en incidentes.
         Si existe → devuelve incidente existente sin crear nada.
      2. También busca por (tenant_id, client_uuid) en sincronizacion_offline.
         Si existe y sincronizado → devuelve incidente vinculado.
      3. Si no existe: crea incidente + registro sincronizacion_offline.

    El cliente puede llamar N veces con el mismo client_uuid: siempre obtiene
    el mismo incidente_id de vuelta, sin duplicados.
    """
    cliente = await _get_cliente_o_403(usuario_id, db)
    now = _utcnow()

    # ── Paso 1: ¿ya existe el incidente con este client_uuid para el tenant? ──
    result_inc = await db.execute(
        select(Incidente).where(
            Incidente.tenant_id == tenant_id,
            Incidente.client_uuid == body.client_uuid,
        )
    )
    inc_existente = result_inc.scalar_one_or_none()
    if inc_existente is not None:
        # Anti-duplicado: devolvemos el existente
        return SyncIncidenteResultado(
            client_uuid=body.client_uuid,
            incidente_id=inc_existente.id,
            creado_nuevo=False,
            estado=inc_existente.estado.value,
            mensaje="Incidente ya sincronizado previamente (anti-duplicado)",
        )

    # ── Paso 2: ¿ya hay registro en sincronizacion_offline? ──────────────────
    result_sync = await db.execute(
        select(SincronizacionOffline).where(
            SincronizacionOffline.tenant_id == tenant_id,
            SincronizacionOffline.client_uuid == body.client_uuid,
        )
    )
    sync_existente = result_sync.scalar_one_or_none()
    if sync_existente is not None and sync_existente.incidente_id is not None:
        return SyncIncidenteResultado(
            client_uuid=body.client_uuid,
            incidente_id=sync_existente.incidente_id,
            creado_nuevo=False,
            estado="PENDIENTE",
            mensaje="Registro de sincronización ya existe",
        )

    # ── Paso 3: Crear incidente nuevo ─────────────────────────────────────────
    inc = Incidente(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        vehiculo_id=body.vehiculo_id,
        tipo_incidente_id=body.tipo_incidente_id,
        zona_id=body.zona_id,
        descripcion=body.descripcion,
        prioridad=body.prioridad,
        latitud=Decimal(str(body.latitud)) if body.latitud is not None else None,
        longitud=Decimal(str(body.longitud)) if body.longitud is not None else None,
        direccion_referencia=body.direccion_referencia,
        sla_minutos=body.sla_minutos,
        origen=OrigenIncidenteEnum.OFFLINE,
        client_uuid=body.client_uuid,
        sync_estado=SyncEstadoEnum.SINCRONIZADO,
        estado=EstadoIncidenteEnum.PENDIENTE,
        reportado_en=body.registrado_local_en or now,
        creado_en=now,
        actualizado_en=now,
    )
    db.add(inc)
    await db.flush()  # obtiene inc.id

    # Historial inicial
    db.add(IncidenteEstadoHistorial(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        estado_anterior=None,
        estado_nuevo=EstadoIncidenteEnum.PENDIENTE.value,
        usuario_id=usuario_id,
        comentario="Incidente sincronizado desde modo offline",
        creado_en=now,
    ))

    # Evento tiempo real
    db.add(EventoTiempoReal(
        tenant_id=tenant_id,
        incidente_id=inc.id,
        usuario_id=usuario_id,
        canal=f"incidente:{inc.id}",
        tipo_evento="ESTADO_CAMBIADO",
        payload={"estado": "PENDIENTE", "origen": "OFFLINE"},
        emitido_en=now,
    ))

    # Registro de sincronización
    if sync_existente is None:
        sync_rec = SincronizacionOffline(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            entidad="incidente",
            client_uuid=body.client_uuid,
            payload=body.model_dump(mode="json"),
            estado_local="sincronizado",
            intentos=1,
            incidente_id=inc.id,
            registrado_local_en=body.registrado_local_en,
            sincronizado_en=now,
            creado_en=now,
        )
        db.add(sync_rec)
    else:
        sync_existente.estado_local = "sincronizado"
        sync_existente.incidente_id = inc.id
        sync_existente.sincronizado_en = now
        sync_existente.intentos += 1

    await db.flush()

    # Emitir WS (si alguien estuviera conectado antes de la reconexión)
    await ws_manager.broadcast_to_incident(
        incident_id=inc.id,
        event_type="ESTADO_CAMBIADO",
        status="PENDIENTE",
        message="Incidente offline sincronizado",
    )

    return SyncIncidenteResultado(
        client_uuid=body.client_uuid,
        incidente_id=inc.id,
        creado_nuevo=True,
        estado=EstadoIncidenteEnum.PENDIENTE.value,
        mensaje="Incidente offline sincronizado exitosamente",
    )


# ── CU40 — Consultar estado de sincronización ─────────────────────────────────

async def get_estado_sincronizacion(
    usuario_id: int, db: AsyncSession, limit: int = 50
) -> list[SincronizacionOffline]:
    """
    GET /api/sync/status
    Devuelve los registros de sincronización del usuario autenticado.
    """
    result = await db.execute(
        select(SincronizacionOffline)
        .where(SincronizacionOffline.usuario_id == usuario_id)
        .order_by(SincronizacionOffline.creado_en.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── CU42 — Sincronizar eventos offline web ────────────────────────────────────

async def sincronizar_eventos_web(
    eventos: list[WebEventoIn],
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
) -> WebSyncResultado:
    """
    POST /api/sync/web/events
    Procesa una lista de eventos offline capturados por Angular PWA.
    Para cada evento:
      - Verifica que el incidente pertenezca al tenant.
      - Valida anti-duplicado por client_uuid en sincronizacion_offline.
      - Si es ESTADO_CAMBIADO, aplica el cambio real en el incidente.
      - Registra en sincronizacion_offline.
      - Registra errores si algo falla.
    Responde con resumen de sincronizados vs. con error.
    """
    now = _utcnow()
    resultados: list[WebEventoResultado] = []
    sincronizados = 0
    con_error = 0

    for ev in eventos:
        try:
            resultado = await _procesar_evento_web(ev, usuario_id, tenant_id, db, now)
            resultados.append(resultado)
            if resultado.sincronizado:
                sincronizados += 1
            else:
                con_error += 1
        except Exception as exc:
            con_error += 1
            resultados.append(WebEventoResultado(
                client_uuid=ev.client_uuid,
                incidente_id=ev.incidente_id,
                tipo_evento=ev.tipo_evento,
                sincronizado=False,
                error=str(exc),
            ))

    return WebSyncResultado(
        total=len(eventos),
        sincronizados=sincronizados,
        con_error=con_error,
        detalle=resultados,
    )


async def _procesar_evento_web(
    ev: WebEventoIn,
    usuario_id: int,
    tenant_id: int,
    db: AsyncSession,
    now: datetime,
) -> WebEventoResultado:
    """Procesa un único evento web offline."""
    # Anti-duplicado
    result_sync = await db.execute(
        select(SincronizacionOffline).where(
            SincronizacionOffline.tenant_id == tenant_id,
            SincronizacionOffline.client_uuid == ev.client_uuid,
        )
    )
    sync_existente = result_sync.scalar_one_or_none()
    if sync_existente is not None and sync_existente.estado_local == "sincronizado":
        return WebEventoResultado(
            client_uuid=ev.client_uuid,
            incidente_id=ev.incidente_id,
            tipo_evento=ev.tipo_evento,
            sincronizado=True,
            error=None,
        )

    # Verificar acceso al incidente
    result_inc = await db.execute(
        select(Incidente).where(
            Incidente.id == ev.incidente_id,
            Incidente.tenant_id == tenant_id,
        )
    )
    inc = result_inc.scalar_one_or_none()
    if inc is None:
        raise ValueError(f"Incidente {ev.incidente_id} no encontrado o acceso denegado")

    # Aplicar cambio real si el evento cambia estado
    if ev.tipo_evento == "ESTADO_CAMBIADO" and "nuevo_estado" in ev.payload:
        try:
            nuevo_estado = EstadoIncidenteEnum(ev.payload["nuevo_estado"])
            estado_anterior = inc.estado.value
            inc.estado = nuevo_estado
            inc.actualizado_en = now

            # Timestamp del estado
            from app.modules.ciclo4.incidentes.service import _map_estado_timestamp
            _map_estado_timestamp(inc, nuevo_estado)

            db.add(IncidenteEstadoHistorial(
                tenant_id=tenant_id,
                incidente_id=inc.id,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado.value,
                usuario_id=usuario_id,
                comentario="Cambio de estado sincronizado desde web offline",
                creado_en=now,
            ))

            db.add(EventoTiempoReal(
                tenant_id=tenant_id,
                incidente_id=inc.id,
                usuario_id=usuario_id,
                canal=f"incidente:{inc.id}",
                tipo_evento="ESTADO_CAMBIADO",
                payload={**ev.payload, "origen": "WEB_OFFLINE"},
                emitido_en=now,
            ))

            await ws_manager.broadcast_to_incident(
                incident_id=inc.id,
                event_type="ESTADO_CAMBIADO",
                status=nuevo_estado.value,
                message="Estado sincronizado desde web offline",
            )
        except ValueError as e:
            raise ValueError(f"Estado inválido: {e}") from e

    # Registrar sync
    if sync_existente is None:
        db.add(SincronizacionOffline(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            entidad="evento",
            client_uuid=ev.client_uuid,
            payload=ev.model_dump(mode="json"),
            estado_local="sincronizado",
            intentos=1,
            incidente_id=inc.id,
            registrado_local_en=ev.registrado_local_en,
            sincronizado_en=now,
            creado_en=now,
        ))
    else:
        sync_existente.estado_local = "sincronizado"
        sync_existente.sincronizado_en = now
        sync_existente.intentos += 1

    await db.flush()

    return WebEventoResultado(
        client_uuid=ev.client_uuid,
        incidente_id=ev.incidente_id,
        tipo_evento=ev.tipo_evento,
        sincronizado=True,
        error=None,
    )
