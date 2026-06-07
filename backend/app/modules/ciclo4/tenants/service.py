# Servicio — Tenants (CRUD mínimo para administración)
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ciclo4.tenants.models import Tenant
from app.modules.ciclo4.tenants.schemas import TenantCreateIn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def crear_tenant(body: TenantCreateIn, db: AsyncSession) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un tenant con slug '{body.slug}'",
        )
    t = Tenant(nombre=body.nombre, slug=body.slug, estado=body.estado, creado_en=_utcnow())
    db.add(t)
    await db.flush()
    return t


async def listar_tenants(db: AsyncSession) -> list[Tenant]:
    result = await db.execute(select(Tenant).order_by(Tenant.id))
    return list(result.scalars().all())


async def get_tenant_o_404(tenant_id: int, db: AsyncSession) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return t
