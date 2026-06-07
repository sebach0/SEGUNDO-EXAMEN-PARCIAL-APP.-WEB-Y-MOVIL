# Servicio — Tenants CRUD (CU43)
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.ciclo4.tenants.models import EstadoTenantEnum, Tenant
from app.modules.ciclo4.tenants.schemas import TenantCreateIn, TenantUpdateIn

_ESTADOS_VALIDOS = {e.value for e in EstadoTenantEnum}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validar_estado(estado: str) -> None:
    if estado not in _ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Estado inválido: {estado}. Use ACTIVO, INACTIVO o SUSPENDIDO.",
        )


async def _slug_disponible(db: AsyncSession, slug: str, excluir_id: int | None = None) -> None:
    q = select(Tenant.id).where(Tenant.slug == slug)
    if excluir_id is not None:
        q = q.where(Tenant.id != excluir_id)
    if (await db.execute(q)).scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un tenant con slug '{slug}'",
        )


async def crear_tenant(
    body: TenantCreateIn,
    db: AsyncSession,
    *,
    usuario_id: int | None = None,
) -> Tenant:
    _validar_estado(body.estado)
    await _slug_disponible(db, body.slug)
    now = _utcnow()
    t = Tenant(
        nombre=body.nombre.strip(),
        slug=body.slug.strip().lower(),
        estado=body.estado,
        creado_en=now,
        actualizado_en=now,
    )
    db.add(t)
    await db.flush()
    await registrar_accion(
        db,
        "tenants",
        "tenants",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Tenant creado slug={t.slug} nombre={t.nombre}",
        usuario_id=usuario_id,
        entidad_id=t.id,
    )
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


async def actualizar_tenant(
    tenant_id: int,
    body: TenantUpdateIn,
    db: AsyncSession,
    *,
    usuario_id: int | None = None,
) -> Tenant:
    t = await get_tenant_o_404(tenant_id, db)
    if body.nombre is not None:
        t.nombre = body.nombre.strip()
    if body.slug is not None:
        slug = body.slug.strip().lower()
        await _slug_disponible(db, slug, excluir_id=t.id)
        t.slug = slug
    if body.estado is not None:
        _validar_estado(body.estado)
        t.estado = body.estado
    t.actualizado_en = _utcnow()
    await db.flush()
    await registrar_accion(
        db,
        "tenants",
        "tenants",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Tenant actualizado id={t.id} estado={t.estado}",
        usuario_id=usuario_id,
        entidad_id=t.id,
    )
    return t


async def activar_tenant(
    tenant_id: int,
    db: AsyncSession,
    *,
    usuario_id: int | None = None,
) -> Tenant:
    t = await get_tenant_o_404(tenant_id, db)
    t.estado = EstadoTenantEnum.ACTIVO.value
    t.actualizado_en = _utcnow()
    await db.flush()
    await registrar_accion(
        db,
        "tenants",
        "tenants",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Tenant activado id={t.id}",
        usuario_id=usuario_id,
        entidad_id=t.id,
    )
    return t


async def desactivar_tenant(
    tenant_id: int,
    db: AsyncSession,
    *,
    usuario_id: int | None = None,
) -> Tenant:
    t = await get_tenant_o_404(tenant_id, db)
    t.estado = EstadoTenantEnum.INACTIVO.value
    t.actualizado_en = _utcnow()
    await db.flush()
    await registrar_accion(
        db,
        "tenants",
        "tenants",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Tenant desactivado id={t.id}",
        usuario_id=usuario_id,
        entidad_id=t.id,
    )
    return t
