"""
Tests Ciclo 5 Etapa 1D–E — tenant guard cotizaciones/pagos + schemas (sin BD).
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:4200")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("MAIL_FROM", "test@test.com")
os.environ.setdefault("EMAIL_LINK_BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_PUBLIC_URL", "http://localhost:4200")

import unittest

from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.cotizaciones.schemas import CotizacionRechazarIn, CotizacionRespondIn
from app.modules.cotizaciones.tenant_guard import (
    assert_user_tenant_access,
    effective_tenant_id,
    resolve_tenant_for_cotizacion,
)
from app.modules.pagos_y_comisiones.pagos.schemas import PagoValidateManualIn


class _FakeUser:
    def __init__(self, tenant_id: int | None) -> None:
        self.tenant_id = tenant_id
        self.id = 1


class _FakeSolicitud:
    def __init__(self, tenant_id: int | None) -> None:
        self.tenant_id = tenant_id


class _FakeTaller:
    def __init__(self, tenant_id: int | None) -> None:
        self.tenant_id = tenant_id


class TestTenantGuardCotizaciones(unittest.TestCase):

    def test_effective_tenant_default(self) -> None:
        self.assertEqual(effective_tenant_id(None), 1)
        self.assertEqual(effective_tenant_id(3), 3)

    def test_assert_user_tenant_access_cross_tenant(self) -> None:
        user = _FakeUser(tenant_id=2)
        with self.assertRaises(HTTPException) as ctx:
            assert_user_tenant_access(user, 99, [])
        self.assertEqual(ctx.exception.status_code, 403)

    def test_assert_user_tenant_admin_global(self) -> None:
        user = _FakeUser(tenant_id=2)
        assert_user_tenant_access(user, 99, ["tenants:gestionar"])

    def test_resolve_tenant_for_cotizacion(self) -> None:
        sol = _FakeSolicitud(tenant_id=5)
        self.assertEqual(resolve_tenant_for_cotizacion(sol), 5)
        sol2 = _FakeSolicitud(tenant_id=None)
        taller = _FakeTaller(tenant_id=7)
        self.assertEqual(resolve_tenant_for_cotizacion(sol2, taller), 7)
        self.assertEqual(resolve_tenant_for_cotizacion(sol2), 1)


class TestCotizacionSchemas(unittest.TestCase):

    def test_respond_decision_valida(self) -> None:
        r = CotizacionRespondIn(decision="RECHAZADA", comment="Muy caro")
        self.assertEqual(r.decision, "RECHAZADA")

    def test_respond_decision_invalida(self) -> None:
        with self.assertRaises(ValidationError):
            CotizacionRespondIn(decision="MAYBE")

    def test_rechazar_sin_comentario(self) -> None:
        r = CotizacionRechazarIn()
        self.assertIsNone(r.comment)


class TestPagoAdminSchemas(unittest.TestCase):

    def test_validate_manual_defaults(self) -> None:
        v = PagoValidateManualIn()
        self.assertTrue(v.aprobado)
        self.assertIsNone(v.observacion)


if __name__ == "__main__":
    unittest.main()
