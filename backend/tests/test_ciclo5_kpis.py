"""
Tests Ciclo 5 Etapa 1B — filtros KPI y schemas dashboard.
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
from datetime import date

from app.modules.kpis.filters import KpiFilters, apply_solicitud_filters
from app.modules.kpis.schemas import AdminDashboardKpisRead, SlaSummaryRead
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
import app.modules.clientes_y_vehiculos.clientes.models  # noqa: F401 — registra mapper Cliente
import app.modules.clientes_y_vehiculos.vehiculos.models  # noqa: F401 — registra mapper Vehiculo
from sqlalchemy import select


class TestKpiFilters(unittest.TestCase):

    def test_kpi_filters_dataclass(self) -> None:
        f = KpiFilters(tenant_id=2, desde=date(2026, 1, 1), taller_id=5)
        self.assertEqual(f.tenant_id, 2)
        self.assertEqual(f.taller_id, 5)

    def test_apply_solicitud_filters_tenant(self) -> None:
        f = KpiFilters(tenant_id=1)
        q = apply_solicitud_filters(select(SolicitudEmergencia.id), f)
        compiled = str(q)
        self.assertIn("tenant_id", compiled.lower())


class TestDashboardSchemas(unittest.TestCase):

    def test_admin_dashboard_empty(self) -> None:
        d = AdminDashboardKpisRead(
            tenant_id=1,
            total_incidents=0,
            average_assignment_minutes=None,
            average_arrival_minutes=None,
            average_total_minutes=None,
            active_incidents=0,
            completed_incidents=0,
            cancelled_cases=0,
            sla_compliance_percentage=None,
            incidents_by_type=[],
            incidents_by_zone=[],
            top_workshops=[],
        )
        self.assertEqual(d.total_incidents, 0)

    def test_sla_summary_schema(self) -> None:
        s = SlaSummaryRead(
            total_incidentes=10,
            incidentes_finalizados=8,
            incidentes_cancelados=2,
            cumplimiento_sla_pct=87.5,
            casos_fuera_sla=1,
        )
        self.assertEqual(s.casos_fuera_sla, 1)


if __name__ == "__main__":
    unittest.main()
