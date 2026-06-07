# Router admin — pagos CU49 (listado + validación manual).
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_permisos, require_permission
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.pagos_y_comisiones.pagos import admin_service
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum
from app.modules.pagos_y_comisiones.pagos.schemas import AdminPagoListRead, PagoRead, PagoValidateManualIn

admin_payments_router = APIRouter(
    prefix="/admin/payments",
    tags=["Admin - Pagos (Ciclo 5)"],
)


@admin_payments_router.get(
    "",
    response_model=AdminPagoListRead,
    dependencies=[Depends(require_permission("pagos:admin"))],
)
async def list_payments(
    tenant_id: int | None = Query(None, description="Tenant (solo admin global)"),
    estado: EstadoPagoEnum | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    user, permisos = user_and_perms
    return await admin_service.list_pagos_admin(
        db,
        user=user,
        permisos=permisos,
        tenant_id=tenant_id,
        estado=estado,
        limit=limit,
        offset=offset,
    )


@admin_payments_router.patch(
    "/{pago_id}/validate-manual",
    response_model=PagoRead,
    dependencies=[Depends(require_permission("pagos:admin"))],
)
async def validate_manual_payment(
    pago_id: int,
    body: PagoValidateManualIn,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    user, permisos = user_and_perms
    return await admin_service.validate_manual_pago(
        db,
        user=user,
        permisos=permisos,
        pago_id=pago_id,
        body=body,
    )
