# WebSocket ConnectionManager — Ciclo 4
# =========================================================
# Gestiona conexiones activas agrupadas por incident_id.
# Canal especial ID=0 → feed admin (recibe copias de todos los eventos).
# Es un singleton importado por los servicios y el router.
# =========================================================
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket

_log = logging.getLogger(__name__)

# ID reservado para el canal de monitoreo admin (no es un incidente real)
ADMIN_CHANNEL_ID = 0


class ConnectionManager:
    """
    Mantiene un diccionario { incident_id: [WebSocket, ...] }.
    Thread-safe para asyncio (un único event loop por proceso uvicorn).

    Canal especial:
        ADMIN_CHANNEL_ID (0) — conectado por el panel admin. Recibe copia
        de TODOS los eventos emitidos por broadcast_to_incident.

    Tipos de evento (type) soportados:
        ESTADO_CAMBIADO
        TRACKING_UPDATE
        TALLER_ACEPTO
        TALLER_RECHAZO
        AUXILIO_EN_CAMINO
        SERVICIO_ATENDIDO
        SERVICIO_FINALIZADO
        ETA_ACTUALIZADO
        SERVICIO_RETRASADO
    """

    def __init__(self) -> None:
        # defaultdict(list) = sin fallo si la clave no existe todavía
        self._active: dict[int, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    # ── Ciclo de vida de conexión ──────────────────────────────────────────

    async def connect(self, ws: WebSocket, incident_id: int) -> None:
        await ws.accept()
        async with self._lock:
            self._active[incident_id].append(ws)
        _log.info("WS conectado: incident=%s total=%s", incident_id, len(self._active[incident_id]))

    async def disconnect(self, ws: WebSocket, incident_id: int) -> None:
        async with self._lock:
            conns = self._active.get(incident_id, [])
            if ws in conns:
                conns.remove(ws)
            if not conns:
                self._active.pop(incident_id, None)
        _log.info("WS desconectado: incident=%s", incident_id)

    # ── Difusión de eventos ───────────────────────────────────────────────

    async def broadcast_to_incident(
        self,
        incident_id: int,
        event_type: str,
        status: str | None = None,
        message: str | None = None,
        payload: dict | None = None,
    ) -> None:
        """
        Envía un mensaje JSON a todos los clientes WebSocket conectados al incidente.
        También lo retransmite al canal admin (ADMIN_CHANNEL_ID=0).
        Los clientes desconectados se eliminan silenciosamente.

        Formato del mensaje (WsEventoOut):
        {
            "type": "ESTADO_CAMBIADO",
            "incident_id": 42,
            "status": "EN_CAMINO",
            "message": "El auxilio está en camino",
            "payload": {},
            "emitted_at": "2026-06-03T12:00:00Z"
        }
        """
        data = json.dumps(
            {
                "type": event_type,
                "incident_id": incident_id,
                "status": status,
                "message": message,
                "payload": payload or {},
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        async with self._lock:
            # Canal específico del incidente + canal admin
            targets = list(self._active.get(incident_id, []))
            admin_targets = list(self._active.get(ADMIN_CHANNEL_ID, []))

        dead: list[WebSocket] = []
        for ws in targets + admin_targets:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)

        # Limpiar conexiones muertas
        if dead:
            async with self._lock:
                for ws in dead:
                    for channel_id in (incident_id, ADMIN_CHANNEL_ID):
                        conns = self._active.get(channel_id, [])
                        if ws in conns:
                            conns.remove(ws)

    async def broadcast_to_admin(
        self,
        event_type: str,
        message: str | None = None,
        payload: dict | None = None,
    ) -> None:
        """Emite un evento directamente al canal admin (sin incident_id específico)."""
        data = json.dumps(
            {
                "type": event_type,
                "incident_id": None,
                "status": None,
                "message": message,
                "payload": payload or {},
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        async with self._lock:
            targets = list(self._active.get(ADMIN_CHANNEL_ID, []))

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                conns = self._active.get(ADMIN_CHANNEL_ID, [])
                for ws in dead:
                    if ws in conns:
                        conns.remove(ws)

    async def send_personal(self, ws: WebSocket, data: dict) -> None:
        """Envía un mensaje solo al WebSocket específico (bienvenida, estado inicial)."""
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            pass

    def connected_count(self, incident_id: int) -> int:
        return len(self._active.get(incident_id, []))

    @property
    def admin_connected(self) -> int:
        """Número de conexiones activas en el canal admin."""
        return len(self._active.get(ADMIN_CHANNEL_ID, []))


# Singleton que usan servicios y routers
manager = ConnectionManager()
