# Validaciones multi-tenant y acceso a solicitudes (Ciclo 5).
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.deps import user_can_manage_all_tenants
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.talleres_y_tecnicos.talleres.models import Taller

_DEFAULT_TENANT_ID = 1


def effective_tenant_id(entity_tenant_id: int | None) -> int:
    return entity_tenant_id or _DEFAULT_TENANT_ID


def assert_user_tenant_access(
    user: Usuario,
    resource_tenant_id: int | None,
    permisos: list[str],
) -> None:
    """403 si el usuario no puede acceder al tenant del recurso."""
    if user_can_manage_all_tenants(permisos):
        return
    user_tid = effective_tenant_id(user.tenant_id)
    res_tid = effective_tenant_id(resource_tenant_id)
    if user_tid != res_tid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede acceder a recursos de otro tenant.",
        )


async def get_solicitud_o_404(db: AsyncSession, solicitud_id: int) -> SolicitudEmergencia:
    res = await db.execute(
        select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id)
    )
    sol = res.scalar_one_or_none()
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    return sol


async def assert_cliente_solicitud(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    cliente_id: int,
) -> None:
    if solicitud.cliente_id != cliente_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")


async def assert_taller_mismo_tenant_solicitud(
    db: AsyncSession,
    *,
    solicitud: SolicitudEmergencia,
    taller_id: int,
) -> Taller:
    res = await db.execute(select(Taller).where(Taller.id == taller_id))
    taller = res.scalar_one_or_none()
    if taller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado.")
    return taller


def resolve_tenant_for_cotizacion(
    solicitud: SolicitudEmergencia,
    taller: Taller | None = None,
) -> int:
    if solicitud.tenant_id is not None:
        return solicitud.tenant_id
    if taller is not None and taller.tenant_id is not None:
        return taller.tenant_id
    return _DEFAULT_TENANT_ID
