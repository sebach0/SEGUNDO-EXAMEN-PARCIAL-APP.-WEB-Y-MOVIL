# app/modules/roles/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.roles import service
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.schemas import (
    AsignarPermisosARol,
    RolCreate,
    RolPermisosRead,
    RolRead,
)

roles_router = APIRouter(prefix="/roles", tags=["Roles"])


@roles_router.get("/", response_model=list[RolRead])
async def listar_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.get_roles(db)


@roles_router.post("/", response_model=RolRead, status_code=status.HTTP_201_CREATED)
async def crear_rol(
    body: RolCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.create_rol(body.nombre, body.descripcion, db)


@roles_router.put("/{rol_id}/permisos", status_code=status.HTTP_204_NO_CONTENT)
async def asignar_permisos(
    rol_id: int,
    body: AsignarPermisosARol,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await service.asignar_permisos_rol(rol_id, body.permiso_ids, db)


@roles_router.get("/{rol_id}/permisos", response_model=RolPermisosRead)
async def listar_permiso_ids_de_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    r = await db.execute(select(Rol).where(Rol.id == rol_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    ids = await service.get_permiso_ids_for_rol(rol_id, db)
    return RolPermisosRead(rol_id=rol_id, permiso_ids=ids)
