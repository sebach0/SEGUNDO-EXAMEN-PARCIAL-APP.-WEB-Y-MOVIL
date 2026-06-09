# app/modules/usuarios/router.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.usuarios import service
from app.modules.acceso_y_administracion.roles.schemas import AsignarRolesAUsuario
from app.modules.clientes_y_vehiculos.clientes.schemas import ClienteCreate, ClienteRead
from pydantic import BaseModel, Field
from app.modules.acceso_y_administracion.usuarios.schemas import (
    UsuarioCreate,
    UsuarioRead,
    UsuarioListRead,
    UsuarioUpdate,
)


class ResetPasswordBody(BaseModel):
    password: str = Field(..., min_length=6)
from app.modules.acceso_y_administracion.usuarios.models import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=list[UsuarioListRead])
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.get_usuarios_admin(db)


@router.get("/{usuario_id}", response_model=UsuarioListRead)
async def obtener_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.get_usuario_list_read(usuario_id, db)


@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    body: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.create_usuario(body.model_dump(), db, ejecutor_id=current_user.id)


@router.put("/{usuario_id}", response_model=UsuarioRead)
async def actualizar_usuario(
    usuario_id: int,
    body: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_usuario(
        usuario_id, body.model_dump(exclude_none=True), db, ejecutor_id=current_user.id
    )


@router.post("/{usuario_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password_usuario(
    usuario_id: int,
    body: ResetPasswordBody,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await service.reset_password_usuario(usuario_id, body.password, db, ejecutor_id=current_user.id)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await service.delete_usuario(usuario_id, db, ejecutor_id=current_user.id)


@router.put("/{usuario_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def asignar_roles_a_usuario(
    usuario_id: int,
    body: AsignarRolesAUsuario,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await service.asignar_roles_usuario(usuario_id, body.rol_ids, db, current_user.id)


# ── Clientes ─────────────────────────────────────────────────
clientes_router = APIRouter(prefix="/clientes", tags=["Clientes"])

@clientes_router.get("/", response_model=list[ClienteRead])
async def listar_clientes(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.get_clientes(db)


@clientes_router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    body: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.create_cliente(body.model_dump(), db)
