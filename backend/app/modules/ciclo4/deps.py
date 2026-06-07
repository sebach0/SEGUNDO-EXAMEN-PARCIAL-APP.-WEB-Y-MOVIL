# Dependencias compartidas del módulo Ciclo 4
# =========================================================
# get_tenant_id: extrae el tenant del usuario autenticado.
# Retorna tenant_id=1 (principal) si el usuario no tiene tenant asignado
# (retrocompatibilidad con datos de Ciclo 1-3).
# =========================================================
from __future__ import annotations

from fastapi import Depends

from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.usuarios.models import Usuario

_DEFAULT_TENANT_ID = 1  # tenant "principal" creado por la migración 0015


def get_tenant_id(
    current_user: Usuario = Depends(get_current_user),
) -> int:
    """
    Devuelve el tenant_id del usuario autenticado.
    Si el usuario no tiene tenant asignado (datos Ciclo 1-3) usa el tenant por defecto.
    """
    return current_user.tenant_id or _DEFAULT_TENANT_ID
