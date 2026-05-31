# app/modules/talleres/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.timeutil import utc_now_naive
from app.modules.talleres_y_tecnicos.talleres.models import Taller, Tecnico, EspecialidadTecnico
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum


async def get_talleres(db: AsyncSession):
    result = await db.execute(select(Taller).order_by(Taller.nombre_comercial))
    return list(result.scalars().all())

async def get_taller_by_id(taller_id: int, db: AsyncSession) -> Taller:
    result = await db.execute(select(Taller).where(Taller.id == taller_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return t

async def create_taller(data: dict, db: AsyncSession, ejecutor_id: int | None = None) -> Taller:
    t = Taller(**data, created_at=utc_now_naive(), updated_at=utc_now_naive())
    db.add(t)
    await db.flush()
    await registrar_accion(db=db, usuario_id=ejecutor_id, modulo="talleres", entidad="talleres",
        entidad_id=t.id, accion=AccionBitacoraEnum.CREAR, descripcion=f"Taller creado: {t.nombre_comercial}")
    return t

async def update_taller(taller_id: int, data: dict, db: AsyncSession, ejecutor_id: int | None = None) -> Taller:
    t = await get_taller_by_id(taller_id, db)
    for k, v in data.items():
        if v is not None:
            setattr(t, k, v)
    t.updated_at = utc_now_naive()
    await registrar_accion(db=db, usuario_id=ejecutor_id, modulo="talleres", entidad="talleres",
        entidad_id=taller_id, accion=AccionBitacoraEnum.ACTUALIZAR, descripcion=f"Taller actualizado: {taller_id}")
    return t

async def get_especialidades(db: AsyncSession):
    result = await db.execute(select(EspecialidadTecnico).order_by(EspecialidadTecnico.nombre))
    return list(result.scalars().all())

async def create_especialidad(nombre: str, descripcion: str | None, db: AsyncSession) -> EspecialidadTecnico:
    e = EspecialidadTecnico(nombre=nombre, descripcion=descripcion)
    db.add(e)
    await db.flush()
    return e

async def get_tecnicos(db: AsyncSession, taller_id: int | None = None):
    query = select(Tecnico)
    if taller_id:
        query = query.where(Tecnico.taller_id == taller_id)
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_tecnico(data: dict, db: AsyncSession, ejecutor_id: int | None = None) -> Tecnico:
    t = Tecnico(**data, created_at=utc_now_naive(), updated_at=utc_now_naive())
    db.add(t)
    await db.flush()
    await registrar_accion(db=db, usuario_id=ejecutor_id, modulo="talleres", entidad="tecnicos",
        entidad_id=t.id, accion=AccionBitacoraEnum.CREAR)
    return t

async def update_tecnico(tecnico_id: int, data: dict, db: AsyncSession, ejecutor_id: int | None = None) -> Tecnico:
    result = await db.execute(select(Tecnico).where(Tecnico.id == tecnico_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    for k, v in data.items():
        if v is not None:
            setattr(t, k, v)
    t.updated_at = utc_now_naive()
    return t
