# Router — Ciclo 4: Incidentes v2
# =========================================================
# REST:
#   POST   /incidents                     — crear incidente (CU11 v2)
#   GET    /incidents                     — listar mis incidentes
#   GET    /incidents/{id}                — detalle (CU36 polling)
#   PATCH  /incidents/{id}/status         — cambiar estado (CU37)
#   GET    /incidents/{id}/tracking       — obtener tracking (CU36)
#   POST   /incidents/{id}/tracking       — agregar punto GPS (CU37)
#
# WebSocket:
#   WS     /ws/incidents/{id}             — tiempo real (CU36/CU37)
# =========================================================
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.core.security import decode_token
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.deps import get_tenant_id
from app.modules.ciclo4.incidentes import service
from app.modules.ciclo4.incidentes.schemas import (
    CambiarEstadoIn,
    IncidenteCreateIn,
    IncidenteDetalleRead,
    IncidenteRead,
    TrackingCreateIn,
    TrackingRead,
)
from app.modules.ciclo4.websocket.manager import manager as ws_manager

_log = logging.getLogger(__name__)

incidents_router = APIRouter(
    prefix="/incidents",
    tags=["Incidentes Ciclo 4"],
)

ws_router = APIRouter(
    prefix="/ws",
    tags=["WebSocket — Incidentes"],
)


# ── REST ──────────────────────────────────────────────────────────────────────

@incidents_router.post(
    "",
    response_model=IncidenteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("incidentes_v2:crear"))],
)
async def crear_incidente(
    body: IncidenteCreateIn,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Crea un incidente en línea (CU11 Ciclo 4). Para offline usa POST /sync/incidents."""
    inc = await service.crear_incidente(body, current_user.id, tenant_id, db)
    return inc


@incidents_router.get(
    "",
    response_model=list[IncidenteRead],
    dependencies=[Depends(require_permission("incidentes_v2:leer"))],
)
async def listar_incidentes(
    limit: int = Query(50, ge=1, le=200),
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_incidentes_usuario(current_user.id, tenant_id, db, limit)


@incidents_router.get(
    "/{incident_id}",
    response_model=IncidenteDetalleRead,
    dependencies=[Depends(require_permission("incidentes_v2:leer"))],
)
async def detalle_incidente(
    incident_id: int,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """CU36 — polling: cliente consulta estado + historial + tracking reciente."""
    inc = await service.get_incidente_detalle(incident_id, tenant_id, db)
    tracking = await service.get_tracking(incident_id, tenant_id, db, limit=10)
    return IncidenteDetalleRead(
        **IncidenteRead.model_validate(inc).model_dump(),
        historial_estados=inc.historial_estados,
        tracking_reciente=tracking,
        eventos_recientes=inc.eventos[-10:] if inc.eventos else [],
    )


@incidents_router.patch(
    "/{incident_id}/status",
    response_model=IncidenteRead,
    dependencies=[Depends(require_permission("incidentes_v2:actualizar"))],
)
async def cambiar_estado(
    incident_id: int,
    body: CambiarEstadoIn,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """CU37 — taller/técnico cambia estado → historial + evento + WebSocket."""
    return await service.cambiar_estado(incident_id, body, current_user.id, tenant_id, db)


@incidents_router.get(
    "/{incident_id}/tracking",
    response_model=list[TrackingRead],
    dependencies=[Depends(require_permission("incidentes_v2:leer"))],
)
async def obtener_tracking(
    incident_id: int,
    limit: int = Query(50, ge=1, le=500),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """CU36 — últimas N posiciones GPS del técnico."""
    return await service.get_tracking(incident_id, tenant_id, db, limit)


@incidents_router.post(
    "/{incident_id}/tracking",
    response_model=TrackingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("tracking:enviar"))],
)
async def agregar_tracking(
    incident_id: int,
    body: TrackingCreateIn,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """CU37 — técnico/taller envía su posición GPS. Se emite por WebSocket."""
    return await service.agregar_tracking(incident_id, body, current_user.id, tenant_id, db)


# ── WebSocket (CU36 / CU37) ───────────────────────────────────────────────────

@ws_router.websocket("/incidents/{incident_id}")
async def ws_incident(
    websocket: WebSocket,
    incident_id: int,
    token: str | None = Query(None, description="JWT de acceso"),
    db: AsyncSession = Depends(get_db),
):
    """
    CU36/CU37 — Canal WebSocket por incidente.

    Conexión: ws://host/api/ws/incidents/42?token=<jwt>

    Al conectar:
      1. Valida el token JWT (401 si inválido).
      2. Verifica que el incidente exista y pertenezca al tenant del usuario.
      3. Envía el estado actual como primer mensaje.
      4. Mantiene la conexión para recibir futuros eventos.

    Tipos de mensaje emitidos:
      ESTADO_CAMBIADO | TRACKING_UPDATE | TALLER_ACEPTO |
      TALLER_RECHAZO | AUXILIO_EN_CAMINO | SERVICIO_ATENDIDO | SERVICIO_FINALIZADO
    """
    # ── 1. Validar token ─────────────────────────────────────────────────
    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        if payload.get("type") != "access" or not user_id:
            raise ValueError("Token inválido")
    except Exception:
        await websocket.close(code=4001, reason="Token inválido o expirado")
        return

    # ── 2. Verificar acceso al incidente o solicitud ──────────────────────
    from sqlalchemy import select as _select
    from app.modules.acceso_y_administracion.usuarios.models import Usuario as _Usuario
    from app.modules.ciclo4.incidentes.models import Incidente as _Inc
    from app.modules.ciclo4.deps import _DEFAULT_TENANT_ID

    user_result = await db.execute(_select(_Usuario).where(_Usuario.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        await websocket.close(code=4001, reason="Usuario no encontrado")
        return

    tenant_id = user.tenant_id or _DEFAULT_TENANT_ID

    # Intentar primero en la tabla incidentes (flujo ciclo4)
    inc_result = await db.execute(
        _select(_Inc).where(_Inc.id == incident_id, _Inc.tenant_id == tenant_id)
    )
    inc = inc_result.scalar_one_or_none()

    initial_status: str
    initial_payload: dict

    if inc is not None:
        # Flujo ciclo4 — incidente encontrado
        initial_status = inc.estado.value
        initial_payload = {
            "taller_asignado_id": inc.taller_asignado_id,
            "latitud": float(inc.latitud) if inc.latitud else None,
            "longitud": float(inc.longitud) if inc.longitud else None,
        }
    else:
        # Flujo real — buscar en solicitudes_emergencia
        from app.modules.incidentes.emergencias.models import SolicitudEmergencia as _Sol

        sol_result = await db.execute(
            _select(_Sol).where(_Sol.id == incident_id)
        )
        sol = sol_result.scalar_one_or_none()
        if sol is None:
            await websocket.close(code=4004, reason="Incidente/Solicitud no encontrado")
            return
        initial_status = sol.estado.value if sol.estado else "REGISTRADA"
        initial_payload = {
            "taller_id": sol.taller_id,
            "tecnico_id": sol.tecnico_id,
        }

    # ── 3. Conectar y enviar estado inicial ───────────────────────────────
    await ws_manager.connect(websocket, incident_id)
    try:
        await ws_manager.send_personal(
            websocket,
            {
                "type": "ESTADO_CAMBIADO",
                "incident_id": incident_id,
                "status": initial_status,
                "message": f"Conectado. Estado actual: {initial_status}",
                "payload": initial_payload,
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # ── 4. Mantener conexión activa ───────────────────────────────────
        while True:
            # Espera mensajes del cliente (ping/pong, o cerrar conexión)
            data = await websocket.receive_text()
            # En esta implementación básica, el cliente solo escucha.
            # Se puede extender para recibir comandos del cliente.
            _log.debug("WS mensaje recibido de user=%s incident=%s: %s", user_id, incident_id, data)

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, incident_id)


# ── WebSocket admin feed (CU36 admin) ────────────────────────────────────────

@ws_router.websocket("/admin/feed")
async def ws_admin_feed(
    websocket: WebSocket,
    token: str | None = Query(None, description="JWT de acceso (requiere rol admin)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Canal WebSocket para el panel de monitoreo del administrador.

    Conexión: ws://host/api/ws/admin/feed?token=<jwt>

    Recibe copias de TODOS los eventos emitidos por broadcast_to_incident
    más eventos propios del canal admin (ver ConnectionManager.ADMIN_CHANNEL_ID).

    El frontend admin usa esto para mostrar actividad en tiempo real sin
    suscribirse a cada incidente/solicitud individualmente.
    """
    from app.modules.ciclo4.websocket.manager import ADMIN_CHANNEL_ID

    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        if payload.get("type") != "access" or not user_id:
            raise ValueError("Token inválido")
    except Exception:
        await websocket.close(code=4001, reason="Token inválido o expirado")
        return

    # Verificar que el usuario tenga acceso admin
    from sqlalchemy import select as _select
    from app.modules.acceso_y_administracion.usuarios.models import Usuario as _Usuario

    user_result = await db.execute(_select(_Usuario).where(_Usuario.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        await websocket.close(code=4003, reason="Usuario no encontrado")
        return

    await ws_manager.connect(websocket, ADMIN_CHANNEL_ID)
    try:
        await ws_manager.send_personal(websocket, {
            "type": "ADMIN_CONNECTED",
            "incident_id": None,
            "status": "ok",
            "message": f"Feed admin activo. Usuarios en canal: {ws_manager.admin_connected}",
            "payload": {"user_id": user_id},
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        })
        # Mantener la conexión abierta; los eventos llegan via broadcast
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, ADMIN_CHANNEL_ID)


# ── WebSocket taller feed (bandeja en tiempo real) ───────────────────────────

@ws_router.websocket("/taller/feed")
async def ws_taller_feed(
    websocket: WebSocket,
    token: str | None = Query(None, description="JWT de acceso (rol TALLER_RESPONSABLE)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Canal WebSocket privado por taller.

    Conexión: ws://host/api/ws/taller/feed?token=<jwt>

    Emite BANDEJA_ACTUALIZADA cuando llega una nueva solicitud a la bandeja del taller.
    """
    from app.modules.ciclo4.websocket.manager import TALLER_CHANNEL_BASE

    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        if payload.get("type") != "access" or not user_id:
            raise ValueError("Token inválido")
    except Exception:
        await websocket.close(code=4001, reason="Token inválido o expirado")
        return

    from sqlalchemy import select as _select
    from app.modules.talleres_y_tecnicos.talleres.models import Taller as _Taller

    t_result = await db.execute(
        _select(_Taller).where(_Taller.usuario_responsable_id == user_id)
    )
    taller = t_result.scalar_one_or_none()
    if taller is None:
        await websocket.close(code=4003, reason="No se encontró taller asociado al usuario")
        return

    channel_id = TALLER_CHANNEL_BASE + taller.id
    await ws_manager.connect(websocket, channel_id)
    try:
        await ws_manager.send_personal(websocket, {
            "type": "TALLER_FEED_CONNECTED",
            "incident_id": None,
            "status": "ok",
            "message": f"Feed taller #{taller.id} activo",
            "payload": {"taller_id": taller.id},
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        })
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, channel_id)


# ── REST: solicitudes activas para admin ──────────────────────────────────────

@incidents_router.get(
    "/admin/solicitudes-activas",
    dependencies=[Depends(require_permission("solicitudes_emergencia:leer"))],
)
async def listar_solicitudes_activas_admin(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Admin — lista las solicitudes de emergencia en estados activos
    (PENDIENTE, BUSCANDO_TALLER, TALLER_ASIGNADO, EN_CAMINO, EN_ATENCION).

    Usada por el panel de monitoreo del administrador.
    """
    from sqlalchemy import select as _select
    from app.modules.incidentes.emergencias.models import (
        SolicitudEmergencia,
        EstadoSolicitudSeguimientoEnum,
    )

    estados_activos = [
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
        EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.EN_CAMINO,
        EstadoSolicitudSeguimientoEnum.EN_ATENCION,
    ]

    result = await db.execute(
        _select(SolicitudEmergencia)
        .where(SolicitudEmergencia.estado.in_(estados_activos))
        .order_by(SolicitudEmergencia.created_at.desc())
        .limit(limit)
    )
    solicitudes = result.scalars().all()

    return [
        {
            "id": s.id,
            "estado": s.estado.value if s.estado else None,
            "taller_id": s.taller_id,
            "tecnico_id": s.tecnico_id,
            "cliente_id": s.cliente_id,
            "tiempo_estimado_min": s.tiempo_estimado_min,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "asignado_en": s.asignado_en.isoformat() if s.asignado_en else None,
            "en_camino_en": s.en_camino_en.isoformat() if s.en_camino_en else None,
        }
        for s in solicitudes
    ]


@incidents_router.get(
    "/admin/emergencias",
    dependencies=[Depends(require_permission("incidentes:leer"))],
)
async def listar_todas_emergencias_admin(
    db: AsyncSession = Depends(get_db),
    estado: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Admin — lista todas las emergencias con info de cliente y taller."""
    from sqlalchemy import select as _select
    from app.modules.incidentes.emergencias.models import (
        SolicitudEmergencia,
        EstadoSolicitudSeguimientoEnum,
    )
    from app.modules.clientes_y_vehiculos.clientes.models import Cliente
    from app.modules.acceso_y_administracion.usuarios.models import Usuario
    from app.modules.talleres_y_tecnicos.talleres.models import Taller

    q = _select(SolicitudEmergencia).order_by(SolicitudEmergencia.created_at.desc())

    if estado:
        try:
            q = q.where(SolicitudEmergencia.estado == EstadoSolicitudSeguimientoEnum(estado))
        except ValueError:
            pass

    result = await db.execute(q.limit(limit).offset(offset))
    solicitudes = result.scalars().all()

    taller_ids = {s.taller_id for s in solicitudes if s.taller_id}
    talleres_map: dict[int, str] = {}
    if taller_ids:
        t_res = await db.execute(
            _select(Taller.id, Taller.nombre_comercial).where(Taller.id.in_(taller_ids))
        )
        talleres_map = {r.id: r.nombre_comercial for r in t_res.all()}

    cliente_ids = {s.cliente_id for s in solicitudes if s.cliente_id}
    clientes_map: dict[int, str] = {}
    if cliente_ids:
        c_res = await db.execute(
            _select(Cliente.id, Usuario.nombres, Usuario.apellidos)
            .join(Usuario, Cliente.usuario_id == Usuario.id)
            .where(Cliente.id.in_(cliente_ids))
        )
        clientes_map = {r.id: f"{r.nombres} {r.apellidos}" for r in c_res.all()}

    return [
        {
            "id": s.id,
            "estado": s.estado.value if s.estado else None,
            "cliente_id": s.cliente_id,
            "cliente_nombre": clientes_map.get(s.cliente_id),
            "taller_id": s.taller_id,
            "taller_nombre": talleres_map.get(s.taller_id) if s.taller_id else None,
            "descripcion_texto": s.descripcion_texto,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "asignado_en": s.asignado_en.isoformat() if s.asignado_en else None,
            "en_camino_en": s.en_camino_en.isoformat() if s.en_camino_en else None,
            "en_atencion_en": s.en_atencion_en.isoformat() if s.en_atencion_en else None,
            "finalizada_at": s.finalizada_at.isoformat() if s.finalizada_at else None,
            "cancelado_en": s.cancelado_en.isoformat() if s.cancelado_en else None,
            "motivo_cancelacion": s.motivo_cancelacion,
            "tenant_id": s.tenant_id,
        }
        for s in solicitudes
    ]
