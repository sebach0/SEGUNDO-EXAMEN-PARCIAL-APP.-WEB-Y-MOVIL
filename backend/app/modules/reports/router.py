# Router — Reportes admin (CU46)
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum
from app.modules.kpis.deps import get_kpi_filters
from app.modules.kpis.filters import KpiFilters
from app.modules.reports import service
from app.modules.reports.schemas import (
    CancellationReportRead,
    IncidentReportRead,
    PerformanceReportRead,
    WorkshopReportRead,
)

reports_router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin - Reportes (Ciclo 5)"],
)


@reports_router.get(
    "/incidents",
    response_model=IncidentReportRead,
    dependencies=[Depends(require_permission("reports:leer"))],
)
async def report_incidents(
    filters: KpiFilters = Depends(get_kpi_filters),
    estado: str | None = Query(None, description="Filtrar por estado de solicitud"),
    db: AsyncSession = Depends(get_db),
):
    estado_enum = None
    if estado is not None:
        try:
            estado_enum = EstadoSolicitudSeguimientoEnum(estado.upper())
        except ValueError:
            from fastapi import HTTPException

            raise HTTPException(status_code=422, detail=f"Estado inválido: {estado}")
    return await service.get_incidents_report(db, filters, estado=estado_enum)


@reports_router.get(
    "/performance",
    response_model=PerformanceReportRead,
    dependencies=[Depends(require_permission("reports:leer"))],
)
async def report_performance(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_performance_report(db, filters)


@reports_router.get(
    "/workshops",
    response_model=WorkshopReportRead,
    dependencies=[Depends(require_permission("reports:leer"))],
)
async def report_workshops(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_workshops_report(db, filters)


@reports_router.get(
    "/cancellations",
    response_model=CancellationReportRead,
    dependencies=[Depends(require_permission("reports:leer"))],
)
async def report_cancellations(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_cancellations_report(db, filters)


@reports_router.get(
    "/export/csv",
    dependencies=[Depends(require_permission("reports:exportar"))],
)
async def export_incidents_csv(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    csv_content = await service.export_incidents_csv(db, filters)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_incidentes.csv"},
    )
