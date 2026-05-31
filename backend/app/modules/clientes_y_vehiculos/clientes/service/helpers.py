from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.roles.models import Rol


async def rol_id_por_nombre(db: AsyncSession, nombre: str) -> int:
    r = await db.execute(select(Rol.id).where(Rol.nombre == nombre))
    row = r.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rol '{nombre}' no configurado en el sistema.",
        )
    return int(row)
