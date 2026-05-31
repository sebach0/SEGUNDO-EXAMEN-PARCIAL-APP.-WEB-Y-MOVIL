# app/modules/usuarios/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum


class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    telefono: str
    password: str
    username: Optional[str] = None
    estado: EstadoUsuarioEnum = EstadoUsuarioEnum.ACTIVO


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombres: str
    apellidos: str
    username: Optional[str]
    email: str
    telefono: str
    estado: EstadoUsuarioEnum
    ultimo_acceso_at: Optional[datetime]
    created_at: Optional[datetime]


class UsuarioListRead(UsuarioRead):
    """Listado admin: incluye nombres de roles."""

    roles: list[str] = []


class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    username: Optional[str] = None
    estado: Optional[EstadoUsuarioEnum] = None
