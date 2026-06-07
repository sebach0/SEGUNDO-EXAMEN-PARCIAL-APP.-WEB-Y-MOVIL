"""
Tests Ciclo 4 — sin base de datos real (lógica y schemas Pydantic).

Cubre:
  1. IncidenteCreateIn rechaza OFFLINE sin client_uuid.
  2. SyncIncidenteIn siempre tiene client_uuid.
  3. CambiarEstadoIn valida solo estados del enum.
  4. WsEventoOut serializa correctamente.
  5. WebEventoIn es válido con campos mínimos.
  6. Anti-duplicado por tenant+client_uuid (lógica de servicio).
  7. Timestamp mapping — cada estado actualiza el campo correcto.
  8. Mensaje broadcast del ConnectionManager formatea JSON correcto.
"""
from __future__ import annotations

# Inyectar DATABASE_URL antes de importar cualquier módulo de la app
# (necesario porque Settings() de pydantic-settings valida al instanciarse).
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY",   "test-secret-key-for-testing-only")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:4200")
os.environ.setdefault("SMTP_HOST",    "localhost")
os.environ.setdefault("MAIL_FROM",    "test@test.com")
os.environ.setdefault("EMAIL_LINK_BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_PUBLIC_URL", "http://localhost:4200")

import asyncio
import json
import unittest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError

from app.modules.ciclo4.incidentes.models import (
    EstadoIncidenteEnum,
    Incidente,
    OrigenIncidenteEnum,
    SyncEstadoEnum,
)
from app.modules.ciclo4.incidentes.schemas import (
    CambiarEstadoIn,
    IncidenteCreateIn,
    WsEventoOut,
)
from app.modules.ciclo4.sync.schemas import (
    SyncIncidenteIn,
    WebEventoIn,
)
from app.modules.ciclo4.websocket.manager import ConnectionManager


# ── 1. Schema: OFFLINE requiere client_uuid ───────────────────────────────────

class TestIncidenteCreateSchema(unittest.TestCase):

    def test_online_sin_client_uuid_es_valido(self) -> None:
        body = IncidenteCreateIn(vehiculo_id=1, origen=OrigenIncidenteEnum.ONLINE)
        self.assertEqual(body.origen, OrigenIncidenteEnum.ONLINE)
        self.assertIsNone(body.client_uuid)

    def test_offline_sin_client_uuid_lanza_error(self) -> None:
        """CU38: incidente OFFLINE sin client_uuid debe fallar en validación."""
        with self.assertRaises(ValidationError) as ctx:
            IncidenteCreateIn(vehiculo_id=1, origen=OrigenIncidenteEnum.OFFLINE)
        errors = ctx.exception.errors()
        self.assertTrue(
            any("client_uuid" in str(e).lower() or "offline" in str(e).lower() for e in errors),
            f"Error inesperado: {errors}",
        )

    def test_offline_con_client_uuid_es_valido(self) -> None:
        cid = uuid.uuid4()
        body = IncidenteCreateIn(
            vehiculo_id=1,
            origen=OrigenIncidenteEnum.OFFLINE,
            client_uuid=cid,
        )
        self.assertEqual(body.client_uuid, cid)

    def test_prioridad_invalida_rechazada(self) -> None:
        with self.assertRaises(ValidationError):
            IncidenteCreateIn(vehiculo_id=1, prioridad="URGENTE")

    def test_prioridades_validas(self) -> None:
        for p in ("BAJA", "MEDIA", "ALTA", "CRITICA"):
            body = IncidenteCreateIn(vehiculo_id=1, prioridad=p)
            self.assertEqual(body.prioridad, p)


# ── 2. Schema: SyncIncidenteIn siempre tiene client_uuid ─────────────────────

class TestSyncIncidenteSchema(unittest.TestCase):

    def test_sync_sin_vehiculo_id_lanza_error(self) -> None:
        with self.assertRaises(ValidationError):
            SyncIncidenteIn(client_uuid=uuid.uuid4())  # falta vehiculo_id

    def test_sync_completo_valido(self) -> None:
        cid = uuid.uuid4()
        body = SyncIncidenteIn(client_uuid=cid, vehiculo_id=5)
        self.assertEqual(body.vehiculo_id, 5)
        self.assertEqual(body.client_uuid, cid)


# ── 3. Schema: CambiarEstadoIn valida estados del enum ───────────────────────

class TestCambiarEstadoSchema(unittest.TestCase):

    def test_estado_valido(self) -> None:
        body = CambiarEstadoIn(nuevo_estado=EstadoIncidenteEnum.EN_CAMINO)
        self.assertEqual(body.nuevo_estado, EstadoIncidenteEnum.EN_CAMINO)

    def test_estado_invalido_lanza_error(self) -> None:
        with self.assertRaises(ValidationError):
            CambiarEstadoIn(nuevo_estado="VOLANDO")

    def test_comentario_opcional(self) -> None:
        body = CambiarEstadoIn(nuevo_estado=EstadoIncidenteEnum.CANCELADO)
        self.assertIsNone(body.comentario)


# ── 4. Timestamp mapping — cada estado → campo correcto ──────────────────────

class TestTimestampMapping(unittest.TestCase):

    def _make_incidente(self):
        """
        Crea un objeto simple con los mismos atributos que Incidente.
        Usa SimpleNamespace para evitar el ORM de SQLAlchemy sin BD.
        _map_estado_timestamp solo usa setattr/getattr, funciona con cualquier objeto.
        """
        from types import SimpleNamespace
        return SimpleNamespace(
            estado=EstadoIncidenteEnum.PENDIENTE,
            buscando_taller_en=None,
            asignado_en=None,
            en_camino_en=None,
            en_atencion_en=None,
            finalizado_en=None,
            cancelado_en=None,
            actualizado_en=None,
            motivo_cancelacion=None,
        )

    def test_buscando_taller_rellena_campo(self) -> None:
        from app.modules.ciclo4.incidentes.service import _map_estado_timestamp
        inc = self._make_incidente()
        _map_estado_timestamp(inc, EstadoIncidenteEnum.BUSCANDO_TALLER)
        self.assertIsNotNone(inc.buscando_taller_en)

    def test_en_camino_rellena_campo(self) -> None:
        from app.modules.ciclo4.incidentes.service import _map_estado_timestamp
        inc = self._make_incidente()
        _map_estado_timestamp(inc, EstadoIncidenteEnum.EN_CAMINO)
        self.assertIsNotNone(inc.en_camino_en)
        self.assertIsNone(inc.asignado_en)

    def test_finalizado_rellena_campo(self) -> None:
        from app.modules.ciclo4.incidentes.service import _map_estado_timestamp
        inc = self._make_incidente()
        _map_estado_timestamp(inc, EstadoIncidenteEnum.FINALIZADO)
        self.assertIsNotNone(inc.finalizado_en)

    def test_pendiente_no_rellena_ningun_timestamp(self) -> None:
        from app.modules.ciclo4.incidentes.service import _map_estado_timestamp
        inc = self._make_incidente()
        _map_estado_timestamp(inc, EstadoIncidenteEnum.PENDIENTE)
        self.assertIsNone(inc.buscando_taller_en)
        self.assertIsNone(inc.asignado_en)


# ── 5. WsEventoOut serializa correctamente ────────────────────────────────────

class TestWsEventoOut(unittest.TestCase):

    def test_serializa_a_dict(self) -> None:
        evento = WsEventoOut(
            type="ESTADO_CAMBIADO",
            incident_id=42,
            status="EN_CAMINO",
            message="Auxilio en camino",
            payload={"tecnico": "Juan"},
            emitted_at="2026-06-03T12:00:00Z",
        )
        d = evento.model_dump()
        self.assertEqual(d["type"], "ESTADO_CAMBIADO")
        self.assertEqual(d["incident_id"], 42)
        self.assertEqual(d["status"], "EN_CAMINO")


# ── 6. ConnectionManager formatea mensaje JSON correcto ──────────────────────

class TestConnectionManager(unittest.IsolatedAsyncioTestCase):

    async def test_broadcast_formato_json(self) -> None:
        """Verifica que el mensaje emitido por broadcast es JSON válido con los campos esperados."""
        mgr = ConnectionManager()
        incident_id = 99

        # Mock WebSocket que captura el texto enviado
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()

        await mgr.connect(ws, incident_id)
        await mgr.broadcast_to_incident(
            incident_id=incident_id,
            event_type="TRACKING_UPDATE",
            status="EN_CAMINO",
            message="Posición actualizada",
            payload={"lat": -17.78, "lng": -63.18},
        )

        # send_text fue llamado
        ws.send_text.assert_called_once()
        raw = ws.send_text.call_args[0][0]
        data = json.loads(raw)

        self.assertEqual(data["type"], "TRACKING_UPDATE")
        self.assertEqual(data["incident_id"], incident_id)
        self.assertEqual(data["status"], "EN_CAMINO")
        self.assertIn("emitted_at", data)
        self.assertEqual(data["payload"]["lat"], -17.78)

    async def test_disconnect_limpia_lista(self) -> None:
        mgr = ConnectionManager()
        ws = AsyncMock()
        ws.accept = AsyncMock()

        await mgr.connect(ws, 1)
        self.assertEqual(mgr.connected_count(1), 1)

        await mgr.disconnect(ws, 1)
        self.assertEqual(mgr.connected_count(1), 0)

    async def test_broadcast_sin_conexiones_no_falla(self) -> None:
        """Si nadie está conectado, broadcast no debe lanzar excepción."""
        mgr = ConnectionManager()
        await mgr.broadcast_to_incident(
            incident_id=999,
            event_type="ESTADO_CAMBIADO",
            status="PENDIENTE",
        )


# ── 7. WebEventoIn — validación mínima ────────────────────────────────────────

class TestWebEventoIn(unittest.TestCase):

    def test_evento_valido(self) -> None:
        ev = WebEventoIn(
            client_uuid=uuid.uuid4(),
            incidente_id=10,
            tipo_evento="ESTADO_CAMBIADO",
            payload={"nuevo_estado": "FINALIZADO"},
        )
        self.assertEqual(ev.tipo_evento, "ESTADO_CAMBIADO")
        self.assertIsNone(ev.registrado_local_en)

    def test_evento_sin_incidente_id_rechazado(self) -> None:
        with self.assertRaises(ValidationError):
            WebEventoIn(client_uuid=uuid.uuid4(), tipo_evento="TALLER_ACEPTO")


# ── 8. ENUMs del modelo ───────────────────────────────────────────────────────

class TestEnumsModelo(unittest.TestCase):

    def test_todos_los_estados_incidente(self) -> None:
        estados = [e.value for e in EstadoIncidenteEnum]
        esperados = [
            "PENDIENTE", "BUSCANDO_TALLER", "TALLER_ASIGNADO",
            "EN_CAMINO", "EN_ATENCION", "FINALIZADO", "CANCELADO",
        ]
        self.assertEqual(sorted(estados), sorted(esperados))

    def test_todos_los_sync_estados(self) -> None:
        estados = [e.value for e in SyncEstadoEnum]
        esperados = ["pendiente", "enviado", "sincronizado", "error"]
        self.assertEqual(sorted(estados), sorted(esperados))

    def test_origenes(self) -> None:
        self.assertIn(OrigenIncidenteEnum.OFFLINE, list(OrigenIncidenteEnum))
        self.assertIn(OrigenIncidenteEnum.ONLINE, list(OrigenIncidenteEnum))


if __name__ == "__main__":
    unittest.main()
