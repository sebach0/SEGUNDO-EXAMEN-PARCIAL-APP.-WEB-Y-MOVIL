# Router — SLA por taller (CU50)
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.kpis.deps import get_kpi_filters
from app.modules.kpis.filters import KpiFilters
from app.modules.sla import service
from app.modules.sla.schemas import WorkshopSlaDetailRead, WorkshopSlaRead

sla_router = APIRouter(
    prefix="/admin/sla",
    tags=["Admin - SLA (Ciclo 5)"],
)


@sla_router.get(
    "/workshops",
    response_model=list[WorkshopSlaRead],
    dependencies=[Depends(require_permission("sla:leer"))],
)
async def list_workshops_sla(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_workshops_sla(db, filters)


@sla_router.get(
    "/workshops/{workshop_id}",
    response_model=WorkshopSlaDetailRead,
    dependencies=[Depends(require_permission("sla:leer"))],
)
async def get_workshop_sla_detail(
    workshop_id: int,
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_workshop_sla_detail(db, filters, workshop_id)
