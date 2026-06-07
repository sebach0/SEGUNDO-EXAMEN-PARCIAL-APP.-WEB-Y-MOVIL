# Router — Admin dashboard KPIs (CU45)
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.kpis import service
from app.modules.kpis.deps import get_kpi_filters
from app.modules.kpis.filters import KpiFilters
from app.modules.kpis.schemas import (
    AdminDashboardKpisRead,
    CancelledCaseRead,
    IncidentByTypeRead,
    SlaSummaryRead,
    TallerEficiente,
    ZonaIncidencia,
)

admin_dashboard_router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin - Dashboard KPIs (Ciclo 5)"],
)


@admin_dashboard_router.get(
    "/kpis",
    response_model=AdminDashboardKpisRead,
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_kpis(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_admin_dashboard_kpis(db, filters)


@admin_dashboard_router.get(
    "/incidents-by-type",
    response_model=list[IncidentByTypeRead],
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_incidents_by_type(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_incidents_by_type(db, filters)


@admin_dashboard_router.get(
    "/workshop-efficiency",
    response_model=list[TallerEficiente],
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_workshop_efficiency(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_workshop_efficiency(db, filters)


@admin_dashboard_router.get(
    "/incidents-by-zone",
    response_model=list[ZonaIncidencia],
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_incidents_by_zone(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_incidents_by_zone(db, filters)


@admin_dashboard_router.get(
    "/cancelled-cases",
    response_model=list[CancelledCaseRead],
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_cancelled_cases(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_cancelled_cases(db, filters)


@admin_dashboard_router.get(
    "/sla-summary",
    response_model=SlaSummaryRead,
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def dashboard_sla_summary(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_sla_summary(db, filters)
