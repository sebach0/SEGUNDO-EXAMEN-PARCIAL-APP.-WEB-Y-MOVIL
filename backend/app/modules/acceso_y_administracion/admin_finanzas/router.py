from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.admin_finanzas import service
from app.modules.acceso_y_administracion.admin_finanzas.schemas import (
    AdminFinanzasReportes,
    AdminFinanzasResumen,
)

router = APIRouter(prefix="/admin/finanzas", tags=["Admin - Finanzas"])


@router.get("/resumen", response_model=AdminFinanzasResumen)
async def obtener_finanzas_resumen(
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> AdminFinanzasResumen:
    data = await service.get_finanzas_resumen(db, desde=desde, hasta=hasta)
    return AdminFinanzasResumen.model_validate(data)


@router.get("/reportes", response_model=AdminFinanzasReportes)
async def obtener_finanzas_reportes(
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> AdminFinanzasReportes:
    data = await service.get_finanzas_reportes(db, desde=desde, hasta=hasta)
    return AdminFinanzasReportes.model_validate(data)

