# app/modules/auth/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.acceso_y_administracion.auth.models import EstadoSesionEnum


class LoginRequest(BaseModel):
    """Credenciales para iniciar sesión. Acepta email o username."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta exitosa de autenticación."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SolicitarRecuperacionIn(BaseModel):
    """Solicitud de correo con enlace para restablecer contraseña."""

    email: str


class RestablecerPasswordIn(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=6, max_length=128)


class SesionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    ip_address: Optional[str] = None
    dispositivo: Optional[str] = None
    plataforma: Optional[str] = None
    iniciado_at: datetime
    cerrado_at: Optional[datetime] = None
    estado: EstadoSesionEnum


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombres: str
    apellidos: str
    email: str
    username: Optional[str] = None
    roles: list[str] = []
    permisos: list[str] = []
