# app/modules/bitacora/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum


class BitacoraRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int]
    modulo: str
    entidad: str
    entidad_id: Optional[int]
    accion: AccionBitacoraEnum
    descripcion: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class BitacoraFiltros(BaseModel):
    """Filtros opcionales para consultar la bitácora."""
    usuario_id: Optional[int] = None
    modulo: Optional[str] = None
    accion: Optional[AccionBitacoraEnum] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
