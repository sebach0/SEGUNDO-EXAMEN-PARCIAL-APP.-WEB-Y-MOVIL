# app/modules/vehiculos/router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.clientes_y_vehiculos.vehiculos import service
from app.modules.clientes_y_vehiculos.vehiculos.schemas import (
    MarcaCreate, MarcaRead, ModeloCreate, ModeloRead,
    TipoVehiculoCreate, TipoVehiculoRead,
    VehiculoCreate, VehiculoRead, VehiculoUpdate
)
from app.modules.acceso_y_administracion.usuarios.models import Usuario

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

# ── Catálogos ────────────────────────────────────────────────
@router.get("/marcas", response_model=list[MarcaRead])
async def listar_marcas(db: AsyncSession = Depends(get_db)):
    return await service.get_marcas(db)

@router.post("/marcas", response_model=MarcaRead, status_code=201)
async def crear_marca(body: MarcaCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.create_marca(body.nombre, db)

@router.get("/modelos", response_model=list[ModeloRead])
async def listar_modelos(marca_id: Optional[int] = Query(None), db: AsyncSession = Depends(get_db)):
    return await service.get_modelos(db, marca_id)

@router.post("/modelos", response_model=ModeloRead, status_code=201)
async def crear_modelo(body: ModeloCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.create_modelo(body.marca_id, body.nombre, db)

@router.get("/tipos", response_model=list[TipoVehiculoRead])
async def listar_tipos(db: AsyncSession = Depends(get_db)):
    return await service.get_tipos(db)

@router.post("/tipos", response_model=TipoVehiculoRead, status_code=201)
async def crear_tipo(body: TipoVehiculoCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.create_tipo(body.nombre, db)

# ── Vehículos ────────────────────────────────────────────────
@router.get("/", response_model=list[VehiculoRead])
async def listar_vehiculos(
    cliente_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await service.get_vehiculos(db, cliente_id)

@router.get("/{vehiculo_id}", response_model=VehiculoRead)
async def obtener_vehiculo(vehiculo_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.get_vehiculo_by_id(vehiculo_id, db)

@router.post("/", response_model=VehiculoRead, status_code=201)
async def crear_vehiculo(
    body: VehiculoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.create_vehiculo(body.model_dump(), db, ejecutor_id=current_user.id)

@router.put("/{vehiculo_id}", response_model=VehiculoRead)
async def actualizar_vehiculo(
    vehiculo_id: int,
    body: VehiculoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await service.update_vehiculo(vehiculo_id, body.model_dump(exclude_none=True), db, current_user.id)
