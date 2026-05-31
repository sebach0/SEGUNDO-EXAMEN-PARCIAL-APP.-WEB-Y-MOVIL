# app/modules/permisos/service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.permisos.models import Permiso


async def get_permisos(db: AsyncSession) -> list[Permiso]:
    result = await db.execute(select(Permiso).order_by(Permiso.modulo, Permiso.codigo))
    return list(result.scalars().all())
