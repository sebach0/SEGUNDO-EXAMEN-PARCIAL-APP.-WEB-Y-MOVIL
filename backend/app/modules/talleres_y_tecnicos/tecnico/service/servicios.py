from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.usuarios.models import Usuario

from .. import repository
from ..schemas import ServicioAsignadoRead
from .acceso import get_tecnico_row_for_usuario


async def listar_servicios_asignados(user: Usuario, db: AsyncSession) -> list[ServicioAsignadoRead]:
    t = await get_tecnico_row_for_usuario(user.id, db)
    rows = await repository.list_servicios_asignados_a_tecnico(db, tecnico_id=t.id)
    return [ServicioAsignadoRead.model_validate(r) for r in rows]
