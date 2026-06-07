from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.kpis import service
from app.modules.kpis.deps import get_kpi_filters
from app.modules.kpis.filters import KpiFilters
from app.modules.kpis.schemas import KpiSummaryRead

router = APIRouter(prefix="/kpis", tags=["KPIs operacionales"])


@router.get(
    "/summary",
    response_model=KpiSummaryRead,
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def kpi_summary(
    filters: KpiFilters = Depends(get_kpi_filters),
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard de KPIs operacionales (compatibilidad Ciclo 4).
    Filtra por tenant del usuario o tenant_id explícito (admin global).
    """
    return await service.get_kpi_summary(
        db,
        tenant_id=filters.tenant_id,
        desde=filters.desde,
        hasta=filters.hasta,
        taller_id=filters.taller_id,
        zona_id=filters.zona_id,
        tipo_incidente_id=filters.tipo_incidente_id,
        tipo_incidente_nombre=filters.tipo_incidente_nombre,
    )
