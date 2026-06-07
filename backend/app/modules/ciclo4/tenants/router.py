# Router — Tenants (solo ADMIN)
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.ciclo4.tenants import service
from app.modules.ciclo4.tenants.schemas import TenantCreateIn, TenantRead

tenants_router = APIRouter(
    prefix="/tenants",
    tags=["Tenants (multi-tenant)"],
)


@tenants_router.get(
    "",
    response_model=list[TenantRead],
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def listar_tenants(db: AsyncSession = Depends(get_db)):
    return await service.listar_tenants(db)


@tenants_router.post(
    "",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def crear_tenant(body: TenantCreateIn, db: AsyncSession = Depends(get_db)):
    return await service.crear_tenant(body, db)
