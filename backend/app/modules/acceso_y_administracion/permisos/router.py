# app/modules/permisos/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.permisos import service
from app.modules.acceso_y_administracion.permisos.schemas import PermisoRead

permisos_router = APIRouter(prefix="/permisos", tags=["Permisos"])


@permisos_router.get("/", response_model=list[PermisoRead])
async def listar_permisos(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.get_permisos(db)
