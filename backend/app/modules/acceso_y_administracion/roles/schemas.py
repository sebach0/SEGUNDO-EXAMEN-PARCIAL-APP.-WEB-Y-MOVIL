# app/modules/roles/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RolCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class RolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: Optional[str] = None
    created_at: Optional[datetime] = None


class RolPermisosRead(BaseModel):
    """IDs de permisos asignados al rol (panel admin)."""

    rol_id: int
    permiso_ids: list[int]


class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class AsignarPermisosARol(BaseModel):
    permiso_ids: list[int]


class AsignarRolesAUsuario(BaseModel):
    rol_ids: list[int]
