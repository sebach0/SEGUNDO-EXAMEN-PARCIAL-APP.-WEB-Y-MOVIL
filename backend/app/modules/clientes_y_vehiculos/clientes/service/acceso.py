from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol

from ..models import Cliente


async def get_cliente_row_for_usuario(usuario_id: int, db: AsyncSession) -> Cliente:
    r = await db.execute(select(Cliente).where(Cliente.usuario_id == usuario_id))
    c = r.scalar_one_or_none()
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no tiene perfil de cliente.",
        )
    return c


async def require_cliente_rol(usuario_id: int, db: AsyncSession) -> None:
    r = await db.execute(
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    roles = {row[0] for row in r.fetchall()}
    if "CLIENTE" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo cuentas con rol CLIENTE pueden usar el área de cliente en la app.",
        )
