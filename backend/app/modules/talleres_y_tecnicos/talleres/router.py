# app/modules/talleres/router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.talleres_y_tecnicos.talleres import service
from app.modules.talleres_y_tecnicos.talleres.schemas import (
    TallerCreate, TallerRead, TallerUpdate,
    TecnicoCreate, TecnicoRead, TecnicoUpdate,
    EspecialidadCreate, EspecialidadRead
)
from app.modules.acceso_y_administracion.usuarios.models import Usuario

router = APIRouter(prefix="/talleres", tags=["Talleres"])

@router.get("/", response_model=list[TallerRead])
async def listar_talleres(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.get_talleres(db)

@router.post("/", response_model=TallerRead, status_code=201)
async def crear_taller(body: TallerCreate, db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)):
    return await service.create_taller(body.model_dump(), db, current_user.id)

@router.get("/{taller_id}", response_model=TallerRead)
async def obtener_taller(taller_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.get_taller_by_id(taller_id, db)

@router.put("/{taller_id}", response_model=TallerRead)
async def actualizar_taller(taller_id: int, body: TallerUpdate,
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return await service.update_taller(taller_id, body.model_dump(exclude_none=True), db, current_user.id)

# ── Especialidades ────────────────────────────────────────────
especialidades_router = APIRouter(prefix="/especialidades", tags=["Especialidades"])

@especialidades_router.get("/", response_model=list[EspecialidadRead])
async def listar_especialidades(db: AsyncSession = Depends(get_db)):
    return await service.get_especialidades(db)

@especialidades_router.post("/", response_model=EspecialidadRead, status_code=201)
async def crear_especialidad(body: EspecialidadCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.create_especialidad(body.nombre, body.descripcion, db)

# ── Técnicos ─────────────────────────────────────────────────
tecnicos_router = APIRouter(prefix="/tecnicos", tags=["Técnicos"])

@tecnicos_router.get("/", response_model=list[TecnicoRead])
async def listar_tecnicos(taller_id: Optional[int] = Query(None), db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await service.get_tecnicos(db, taller_id)

@tecnicos_router.post("/", response_model=TecnicoRead, status_code=201)
async def crear_tecnico(body: TecnicoCreate, db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)):
    return await service.create_tecnico(body.model_dump(), db, current_user.id)

@tecnicos_router.put("/{tecnico_id}", response_model=TecnicoRead)
async def actualizar_tecnico(tecnico_id: int, body: TecnicoUpdate,
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return await service.update_tecnico(tecnico_id, body.model_dump(exclude_none=True), db, current_user.id)
