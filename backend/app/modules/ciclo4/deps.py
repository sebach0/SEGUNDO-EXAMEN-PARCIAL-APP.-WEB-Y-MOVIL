# Dependencias compartidas del módulo Ciclo 4 / Ciclo 5 multi-tenant
# =========================================================
# get_tenant_id: tenant efectivo del usuario autenticado.
# resolve_tenant_scope: filtro tenant para consultas admin (CU45+).
# =========================================================
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_current_user_permisos
from app.modules.acceso_y_administracion.usuarios.models import Usuario

_DEFAULT_TENANT_ID = 1  # tenant "principal" creado por la migración 0015
_PERMISO_GESTIONAR_TENANTS = "tenants:gestionar"


def get_tenant_id(
    current_user: Usuario = Depends(get_current_user),
) -> int:
    """
    Devuelve el tenant_id del usuario autenticado.
    Si el usuario no tiene tenant asignado (datos Ciclo 1-3) usa el tenant por defecto.
    """
    return current_user.tenant_id or _DEFAULT_TENANT_ID


def user_can_manage_all_tenants(permisos: list[str]) -> bool:
    """Admin global: puede operar sobre cualquier tenant vía query/path explícito."""
    return _PERMISO_GESTIONAR_TENANTS in permisos


def resolve_tenant_scope(
    current_user: Usuario,
    requested_tenant_id: int | None,
    permisos: list[str],
) -> int:
    """
    Resuelve el tenant_id efectivo para filtros de consulta.

    - Usuario con ``tenants:gestionar`` puede pasar ``requested_tenant_id`` explícito.
    - Sin permiso global, se fuerza el tenant del usuario (nunca cross-tenant).
    """
    if requested_tenant_id is not None:
        if not user_can_manage_all_tenants(permisos):
            user_tid = current_user.tenant_id or _DEFAULT_TENANT_ID
            if requested_tenant_id != user_tid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puede consultar datos de otro tenant.",
                )
        return requested_tenant_id
    return current_user.tenant_id or _DEFAULT_TENANT_ID


async def get_resolved_tenant_id(
    requested_tenant_id: int | None = None,
    user_and_perms: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
) -> int:
    """Dependencia FastAPI para endpoints con filtro tenant opcional."""
    user, permisos = user_and_perms
    return resolve_tenant_scope(user, requested_tenant_id, permisos)
