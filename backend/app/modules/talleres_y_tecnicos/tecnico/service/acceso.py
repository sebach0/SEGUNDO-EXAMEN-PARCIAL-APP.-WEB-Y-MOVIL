from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol
from app.modules.talleres_y_tecnicos.talleres.models import Tecnico


async def require_tecnico_rol(usuario_id: int, db: AsyncSession) -> None:
    r = await db.execute(
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    roles = {row[0] for row in r.fetchall()}
    if "TECNICO" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo cuentas con rol TECNICO pueden usar el área técnico de la app.",
        )


async def get_tecnico_row_for_usuario(usuario_id: int, db: AsyncSession) -> Tecnico:
    r = await db.execute(select(Tecnico).where(Tecnico.usuario_id == usuario_id))
    t = r.scalar_one_or_none()
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no tiene perfil de técnico.",
        )
    return t
