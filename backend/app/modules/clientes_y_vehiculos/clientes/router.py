# API app móvil cliente — registro, perfil, vehículos (`/app/cliente`).
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.vehiculos.schemas import VehiculoRead, VehiculoUpdate

from . import service
from .schemas_movil import (
    ClienteMiPerfilRead,
    ClienteMiPerfilUpdate,
    RegistroClienteMovilIn,
    VehiculoClienteCreateIn,
)

router = APIRouter(prefix="/app/cliente", tags=["App cliente (móvil)"])


@router.post("/registro", response_model=ClienteMiPerfilRead, status_code=status.HTTP_201_CREATED)
async def registro_cliente(body: RegistroClienteMovilIn, db: AsyncSession = Depends(get_db)):
    """Alta pública: usuario + fila cliente + rol CLIENTE."""
    return await service.registro_cliente_publico(body, db)


@router.get("/mi-perfil", response_model=ClienteMiPerfilRead)
async def mi_perfil(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_mi_perfil(current_user, db)


@router.put("/mi-perfil", response_model=ClienteMiPerfilRead)
async def actualizar_mi_perfil(
    body: ClienteMiPerfilUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_mi_perfil(current_user, body, db)


@router.get("/mis-vehiculos", response_model=list[VehiculoRead])
async def mis_vehiculos(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_mis_vehiculos(current_user, db)


@router.get("/mis-vehiculos/{vehiculo_id}", response_model=VehiculoRead)
async def mi_vehiculo(
    vehiculo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_mi_vehiculo(current_user, vehiculo_id, db)


@router.post("/mis-vehiculos", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
async def crear_mi_vehiculo(
    body: VehiculoClienteCreateIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.crear_mi_vehiculo(current_user, body, db)


@router.put("/mis-vehiculos/{vehiculo_id}", response_model=VehiculoRead)
async def actualizar_mi_vehiculo(
    vehiculo_id: int,
    body: VehiculoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.actualizar_mi_vehiculo(current_user, vehiculo_id, body, db)
