"""
Tests Ciclo 5 Etapa 1A — tenants CU43–CU44 (schemas + resolve_tenant_scope).
Sin base de datos real.
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

from app.modules.ciclo4.deps import resolve_tenant_scope, user_can_manage_all_tenants
from app.modules.ciclo4.tenants.schemas import (
    AssignIdsIn,
    TenantCreateIn,
    TenantUpdateIn,
)


class _FakeUser:
    def __init__(self, tenant_id: int | None) -> None:
        self.tenant_id = tenant_id
        self.id = 1


class TestTenantSchemas(unittest.TestCase):

    def test_create_requiere_nombre_y_slug(self) -> None:
        t = TenantCreateIn(nombre="Red Norte", slug="red-norte")
        self.assertEqual(t.estado, "ACTIVO")

    def test_create_slug_invalido(self) -> None:
        with self.assertRaises(ValidationError):
            TenantCreateIn(nombre="X", slug="Red Norte")

    def test_update_vacio_es_valido_pydantic(self) -> None:
        u = TenantUpdateIn()
        self.assertIsNone(u.nombre)

    def test_assign_ids_minimo_uno(self) -> None:
        with self.assertRaises(ValidationError):
            AssignIdsIn(ids=[])


class TestResolveTenantScope(unittest.TestCase):

    def test_admin_global_puede_elegir_tenant(self) -> None:
        user = _FakeUser(tenant_id=1)
        permisos = ["tenants:gestionar"]
        self.assertTrue(user_can_manage_all_tenants(permisos))
        tid = resolve_tenant_scope(user, 5, permisos)
        self.assertEqual(tid, 5)

    def test_usuario_sin_permiso_no_cross_tenant(self) -> None:
        user = _FakeUser(tenant_id=2)
        permisos: list[str] = []
        with self.assertRaises(HTTPException) as ctx:
            resolve_tenant_scope(user, 99, permisos)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_usuario_sin_permiso_usa_su_tenant(self) -> None:
        user = _FakeUser(tenant_id=2)
        tid = resolve_tenant_scope(user, None, [])
        self.assertEqual(tid, 2)

    def test_usuario_sin_tenant_usa_default(self) -> None:
        user = _FakeUser(tenant_id=None)
        tid = resolve_tenant_scope(user, None, [])
        self.assertEqual(tid, 1)


if __name__ == "__main__":
    unittest.main()
