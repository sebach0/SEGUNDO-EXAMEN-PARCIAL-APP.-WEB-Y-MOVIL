# app/modules/vehiculos/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MarcaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class MarcaCreate(BaseModel):
    nombre: str


class ModeloRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    marca_id: int
    nombre: str


class ModeloCreate(BaseModel):
    marca_id: int
    nombre: str


class TipoVehiculoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class TipoVehiculoCreate(BaseModel):
    nombre: str


class VehiculoCreate(BaseModel):
    cliente_id: int
    placa: str
    marca_id: int
    modelo_id: int
    tipo_vehiculo_id: int
    anio: Optional[int] = None
    color: Optional[str] = None


class VehiculoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: int
    placa: str
    marca_id: int
    modelo_id: int
    tipo_vehiculo_id: int
    anio: Optional[int]
    color: Optional[str]
    created_at: Optional[datetime]


class VehiculoUpdate(BaseModel):
    placa: Optional[str] = None
    marca_id: Optional[int] = None
    modelo_id: Optional[int] = None
    tipo_vehiculo_id: Optional[int] = None
    anio: Optional[int] = None
    color: Optional[str] = None
