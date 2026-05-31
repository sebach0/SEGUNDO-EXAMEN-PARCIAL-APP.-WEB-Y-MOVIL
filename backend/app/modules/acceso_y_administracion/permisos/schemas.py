# app/modules/permisos/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PermisoCreate(BaseModel):
    codigo: str
    nombre: str
    modulo: str
    descripcion: Optional[str] = None


class PermisoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    modulo: str
    descripcion: Optional[str] = None
