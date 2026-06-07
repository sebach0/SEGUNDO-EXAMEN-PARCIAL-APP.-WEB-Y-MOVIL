# Tests unitarios — ETA y retraso (solicitudes_emergencia unificadas).
from __future__ import annotations

import asyncio
import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:4200")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("MAIL_FROM", "test@test.com")
os.environ.setdefault("EMAIL_LINK_BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_PUBLIC_URL", "http://localhost:4200")

from app.modules.incidentes.emergencias.eta_service import (
    emit_eta_actualizado_ws,
    minutos_retraso,
)
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum


def _sol(**kwargs):
    base = dict(
        id=1,
        estado=EstadoSolicitudSeguimientoEnum.EN_CAMINO,
        tiempo_estimado_min=30,
        en_camino_en=datetime(2026, 6, 6, 10, 0, 0),
        asignado_en=None,
        tecnico_asignado_at=None,
        eta_origen="MANUAL",
        eta_actualizado_en=datetime(2026, 6, 6, 10, 0, 0),
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestMinutosRetraso(unittest.TestCase):
    def test_sin_eta_retorna_none(self) -> None:
        sol = _sol(tiempo_estimado_min=None)
        self.assertIsNone(minutos_retraso(sol, datetime(2026, 6, 6, 11, 0, 0)))

    def test_dentro_de_eta_es_cero(self) -> None:
        sol = _sol()
        now = sol.en_camino_en + timedelta(minutes=20)
        self.assertEqual(minutos_retraso(sol, now), 0)

    def test_sobre_limite(self) -> None:
        sol = _sol()
        now = sol.en_camino_en + timedelta(minutes=40)
        self.assertEqual(minutos_retraso(sol, now), 10)


class TestEmitEtaWs(unittest.TestCase):
    def test_emit_sin_conexiones_no_falla(self) -> None:
        sol = _sol(tiempo_estimado_min=25)
        asyncio.run(emit_eta_actualizado_ws(sol))


if __name__ == "__main__":
    unittest.main()
