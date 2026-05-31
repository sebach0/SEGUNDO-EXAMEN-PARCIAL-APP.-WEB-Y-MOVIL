# app/modules/talleres/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTallerEnum, EstadoTecnicoEnum


class EspecialidadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    descripcion: Optional[str]

class EspecialidadCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class TallerCreate(BaseModel):
    usuario_responsable_id: int
    nombre_comercial: str
    telefono_contacto: str
    email_contacto: EmailStr
    direccion: str
    ciudad: str
    descripcion: Optional[str] = None
    estado: EstadoTallerEnum = EstadoTallerEnum.PENDIENTE

class TallerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_responsable_id: int
    nombre_comercial: str
    telefono_contacto: str
    email_contacto: str
    direccion: str
    ciudad: str
    descripcion: Optional[str]
    estado: EstadoTallerEnum
    created_at: Optional[datetime]

class TallerUpdate(BaseModel):
    nombre_comercial: Optional[str] = None
    telefono_contacto: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[EstadoTallerEnum] = None


class TecnicoCreate(BaseModel):
    usuario_id: int
    taller_id: int
    especialidad_id: Optional[int] = None
    documento_identidad: Optional[str] = None
    disponibilidad: Optional[str] = None
    estado: EstadoTecnicoEnum = EstadoTecnicoEnum.ACTIVO

class TecnicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_id: int
    taller_id: int
    especialidad_id: Optional[int]
    estado: EstadoTecnicoEnum
    created_at: Optional[datetime]

class TecnicoUpdate(BaseModel):
    taller_id: Optional[int] = None
    especialidad_id: Optional[int] = None
    documento_identidad: Optional[str] = None
    disponibilidad: Optional[str] = None
    estado: Optional[EstadoTecnicoEnum] = None
