# Router — Tenants (CU43–CU44)
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.tenants import service
from app.modules.ciclo4.tenants import service_assignments
from app.modules.ciclo4.tenants.schemas import (
    AssignIdsIn,
    AssignTenantIn,
    AssignmentResultOut,
    TenantCreateIn,
    TenantMembersRead,
    TenantRead,
    TenantUpdateIn,
)

# Legacy — compatibilidad Ciclo 4
tenants_router = APIRouter(
    prefix="/tenants",
    tags=["Tenants (multi-tenant)"],
)

# Ciclo 5 — rutas admin completas
admin_tenants_router = APIRouter(
    prefix="/admin/tenants",
    tags=["Admin - Tenants (Ciclo 5)"],
)

admin_tenant_assign_router = APIRouter(
    prefix="/admin",
    tags=["Admin - Asignación tenant (Ciclo 5)"],
)


# ── Legacy / compat ───────────────────────────────────────────────────────────

@tenants_router.get(
    "/",
    response_model=list[TenantRead],
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def listar_tenants_legacy(db: AsyncSession = Depends(get_db)):
    return await service.listar_tenants(db)


@tenants_router.post(
    "/",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def crear_tenant_legacy(
    body: TenantCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.crear_tenant(body, db, usuario_id=current_user.id)


# ── CU43 — Gestión de tenants ───────────────────────────────────────────────

@admin_tenants_router.get(
    "/",
    response_model=list[TenantRead],
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def listar_tenants(db: AsyncSession = Depends(get_db)):
    return await service.listar_tenants(db)


@admin_tenants_router.get(
    "/{tenant_id}",
    response_model=TenantRead,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def obtener_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_tenant_o_404(tenant_id, db)


@admin_tenants_router.post(
    "/",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def crear_tenant(
    body: TenantCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.crear_tenant(body, db, usuario_id=current_user.id)


@admin_tenants_router.patch(
    "/{tenant_id}",
    response_model=TenantRead,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def actualizar_tenant(
    tenant_id: int,
    body: TenantUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if body.nombre is None and body.slug is None and body.estado is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Debe enviar al menos un campo a actualizar.")
    return await service.actualizar_tenant(
        tenant_id, body, db, usuario_id=current_user.id
    )


@admin_tenants_router.patch(
    "/{tenant_id}/activate",
    response_model=TenantRead,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def activar_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.activar_tenant(tenant_id, db, usuario_id=current_user.id)


@admin_tenants_router.patch(
    "/{tenant_id}/deactivate",
    response_model=TenantRead,
    dependencies=[Depends(require_permission("tenants:gestionar"))],
)
async def desactivar_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.desactivar_tenant(tenant_id, db, usuario_id=current_user.id)


# ── CU44 — Asignación por tenant ──────────────────────────────────────────────

@admin_tenants_router.get(
    "/{tenant_id}/members",
    response_model=TenantMembersRead,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def listar_members(tenant_id: int, db: AsyncSession = Depends(get_db)):
    return await service_assignments.listar_members(tenant_id, db)


@admin_tenants_router.post(
    "/{tenant_id}/assign-users",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def assign_users(
    tenant_id: int,
    body: AssignIdsIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.assign_users(
        tenant_id, body.ids, db, usuario_actor_id=current_user.id
    )


@admin_tenants_router.post(
    "/{tenant_id}/assign-workshops",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def assign_workshops(
    tenant_id: int,
    body: AssignIdsIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.assign_workshops(
        tenant_id, body.ids, db, usuario_actor_id=current_user.id
    )


@admin_tenants_router.post(
    "/{tenant_id}/assign-technicians",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def assign_technicians(
    tenant_id: int,
    body: AssignIdsIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.assign_technicians(
        tenant_id, body.ids, db, usuario_actor_id=current_user.id
    )


@admin_tenant_assign_router.patch(
    "/users/{user_id}/tenant",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def patch_user_tenant(
    user_id: int,
    body: AssignTenantIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.patch_user_tenant(
        user_id, body.tenant_id, db, usuario_actor_id=current_user.id
    )


@admin_tenant_assign_router.patch(
    "/workshops/{workshop_id}/tenant",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def patch_workshop_tenant(
    workshop_id: int,
    body: AssignTenantIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.patch_workshop_tenant(
        workshop_id, body.tenant_id, db, usuario_actor_id=current_user.id
    )


@admin_tenant_assign_router.patch(
    "/technicians/{technician_id}/tenant",
    response_model=AssignmentResultOut,
    dependencies=[Depends(require_permission("tenants:asignar"))],
)
async def patch_technician_tenant(
    technician_id: int,
    body: AssignTenantIn,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service_assignments.patch_technician_tenant(
        technician_id, body.tenant_id, db, usuario_actor_id=current_user.id
    )
