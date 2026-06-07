from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission, get_current_user
from app.modules.kpis import service
from app.modules.kpis.schemas import KpiSummaryRead
from app.modules.acceso_y_administracion.usuarios.models import Usuario

router = APIRouter(prefix="/kpis", tags=["KPIs operacionales"])

_DEFAULT_TENANT_ID = 1


@router.get(
    "/summary",
    response_model=KpiSummaryRead,
    dependencies=[Depends(require_permission("kpis:leer"))],
)
async def kpi_summary(
    desde: date | None = Query(None, description="Fecha inicio inclusive (YYYY-MM-DD)"),
    hasta: date | None = Query(None, description="Fecha fin inclusive (YYYY-MM-DD)"),
    taller_id: int | None = Query(None, description="Filtrar por taller específico"),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard de KPIs operacionales para talleres y redes de talleres.
    Todos los datos provienen de la base de datos (sin hardcodeo).
    Filtra por tenant del usuario autenticado.
    """
    tenant_id: int = current_user.tenant_id or _DEFAULT_TENANT_ID
    return await service.get_kpi_summary(
        db,
        tenant_id=tenant_id,
        desde=desde,
        hasta=hasta,
        taller_id=taller_id,
    )
