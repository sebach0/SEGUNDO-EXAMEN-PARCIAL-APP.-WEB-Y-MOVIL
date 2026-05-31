# app/modules/bitacora/router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.acceso_y_administracion.bitacora.models import Bitacora, AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.schemas import BitacoraRead

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])


@router.get("/", response_model=list[BitacoraRead])
async def listar_bitacora(
    usuario_id: Optional[int] = Query(None),
    modulo: Optional[str] = Query(None),
    accion: Optional[AccionBitacoraEnum] = Query(None),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Consulta la bitácora con filtros opcionales.
    Solo lectura — la bitácora nunca se modifica desde la API.
    """
    query = select(Bitacora).order_by(Bitacora.created_at.desc())

    if usuario_id:
        query = query.where(Bitacora.usuario_id == usuario_id)
    if modulo:
        query = query.where(Bitacora.modulo == modulo)
    if accion:
        query = query.where(Bitacora.accion == accion)
    if desde:
        query = query.where(Bitacora.created_at >= desde)
    if hasta:
        query = query.where(Bitacora.created_at <= hasta)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
