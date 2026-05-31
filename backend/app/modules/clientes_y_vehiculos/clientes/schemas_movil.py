# Schemas Pydantic — API app móvil cliente (`/app/cliente`).
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegistroClienteMovilIn(BaseModel):
    nombres: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=5, max_length=30)
    password: str = Field(..., min_length=6, max_length=128)


class ClienteMiPerfilRead(BaseModel):
    usuario_id: int
    cliente_id: int
    nombres: str
    apellidos: str
    email: str
    telefono: str
    ciudad: str | None
    direccion: str | None
    pendiente_verificacion_email: bool = False


class ClienteMiPerfilUpdate(BaseModel):
    nombres: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=100)
    telefono: str | None = Field(default=None, max_length=30)
    ciudad: str | None = Field(default=None, max_length=100)
    direccion: str | None = None


class VehiculoClienteCreateIn(BaseModel):
    """Alta de vehículo sin cliente_id (se toma del perfil autenticado)."""

    placa: str = Field(..., min_length=2, max_length=20)
    marca_id: int
    modelo_id: int
    tipo_vehiculo_id: int
    anio: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)
