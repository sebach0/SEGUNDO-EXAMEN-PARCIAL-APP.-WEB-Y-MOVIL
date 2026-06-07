from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.modules.talleres_y_tecnicos.talleres.models import EstadoTallerEnum, EstadoTecnicoEnum


class RegistroTallerIn(BaseModel):
    nombre_comercial: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    telefono: str = Field(..., min_length=5, max_length=30)
    direccion: str = Field(..., min_length=3)
    ciudad: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    responsable_nombre_completo: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=4, max_length=128)


class MiTallerUsuarioUpdate(BaseModel):
    nombres: Optional[str] = Field(None, min_length=1, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, min_length=5, max_length=30)


class MiTallerUpdate(BaseModel):
    nombre_comercial: Optional[str] = Field(None, min_length=2, max_length=150)
    telefono_contacto: Optional[str] = Field(None, min_length=5, max_length=30)
    email_contacto: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)
    usuario: Optional[MiTallerUsuarioUpdate] = None


class MiTallerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_comercial: str
    telefono_contacto: str
    email_contacto: str
    direccion: str
    ciudad: str
    descripcion: Optional[str]
    estado: EstadoTallerEnum
    created_at: Optional[datetime]
    responsable_nombres: str
    responsable_apellidos: str
    responsable_email: str
    responsable_telefono: str
    pendiente_verificacion_email: bool = False
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class TecnicoPortalCreate(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    telefono: str = Field(..., min_length=5, max_length=30)
    password: str = Field(..., min_length=4, max_length=128)
    documento: Optional[str] = Field(None, max_length=50)
    especialidad_id: Optional[int] = None
    disponibilidad: Optional[str] = Field(None, max_length=120)
    estado: EstadoTecnicoEnum = EstadoTecnicoEnum.ACTIVO


class TecnicoPortalUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=5, max_length=30)
    documento: Optional[str] = Field(None, max_length=50)
    especialidad_id: Optional[int] = None
    disponibilidad: Optional[str] = Field(None, max_length=120)
    estado: Optional[EstadoTecnicoEnum] = None


class TecnicoPortalRead(BaseModel):
    id: int
    usuario_id: int
    taller_id: int
    nombres: str
    apellidos: str
    email: str
    telefono: str
    documento: Optional[str]
    especialidad_id: Optional[int]
    especialidad_nombre: Optional[str]
    disponibilidad: Optional[str]
    estado: EstadoTecnicoEnum
    created_at: Optional[datetime]
    resumen_actividad: Optional[str] = None


class TallerDashboardRead(BaseModel):
    tecnicos_registrados: int
    tecnicos_activos: int
    disponibilidad_general: str
    taller_estado: EstadoTallerEnum
