# Dependencias FastAPI — filtros KPI / dashboard / reportes.
from __future__ import annotations

from datetime import date

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_permisos
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.deps import resolve_tenant_scope
from app.modules.ciclo4.incidentes.models import TipoIncidente
from app.modules.kpis.filters import KpiFilters


async def get_kpi_filters(
    tenant_id: int | None = Query(None, description="Tenant (solo admin global)"),
    fecha_inicio: date | None = Query(None, alias="desde"),
    fecha_fin: date | None = Query(None, alias="hasta"),
    taller_id: int | None = Query(None),
    zona_id: int | None = Query(None),
    tipo_incidente_id: int | None = Query(None),
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
) -> KpiFilters:
    user, permisos = user_and_perms
    effective_tenant = resolve_tenant_scope(user, tenant_id, permisos)

    tipo_nombre: str | None = None
    if tipo_incidente_id is not None:
        res = await db.execute(
            select(TipoIncidente.nombre).where(TipoIncidente.id == tipo_incidente_id)
        )
        tipo_nombre = res.scalar_one_or_none()
        if tipo_nombre is None:
            raise HTTPException(status_code=404, detail="Tipo de incidente no encontrado")

    return KpiFilters(
        tenant_id=effective_tenant,
        desde=fecha_inicio,
        hasta=fecha_fin,
        taller_id=taller_id,
        zona_id=zona_id,
        tipo_incidente_id=tipo_incidente_id,
        tipo_incidente_nombre=tipo_nombre,
    )
