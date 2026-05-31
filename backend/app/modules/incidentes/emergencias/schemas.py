# Schemas Pydantic — emergencias fase 1
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    TipoEvidenciaSolicitudEnum,
)


class UbicacionCreateIn(BaseModel):
    """CU12 — cuerpo de alta de ubicación."""

    latitud: Decimal = Field(..., ge=Decimal("-90"), le=Decimal("90"))
    longitud: Decimal = Field(..., ge=Decimal("-180"), le=Decimal("180"))
    precision_metros: Decimal | None = Field(None, ge=Decimal("0"))
    direccion_referencia: str | None = Field(None, max_length=2000)
    es_actual: bool = True


class SolicitudEmergenciaCreateIn(BaseModel):
    """CU11 + opcional CU12 inicial + CU15."""

    vehiculo_id: int = Field(..., gt=0)
    descripcion_texto: str | None = Field(None, max_length=8000)
    ubicacion_inicial: UbicacionCreateIn | None = None


class SolicitudEmergenciaUpdateTextoIn(BaseModel):
    """CU15 — solo texto adicional mientras la solicitud siga REGISTRADA."""

    descripcion_texto: str | None = Field(None, max_length=8000)


class EvidenciaCreateIn(BaseModel):
    """CU13 / CU14 — URL del archivo (bucket/CDN); sin multipart en esta fase."""

    tipo: TipoEvidenciaSolicitudEnum
    archivo_url: str = Field(..., min_length=12, max_length=4096)
    mime_type: str | None = Field(None, max_length=100)
    nombre_archivo: str | None = Field(None, max_length=255)
    tamano_bytes: int | None = Field(None, ge=0)

    @field_validator("archivo_url")
    @classmethod
    def https_only(cls, v: str) -> str:
        s = v.strip()
        if not s.lower().startswith("https://"):
            raise ValueError("archivo_url debe ser HTTPS")
        return s

    @model_validator(mode="after")
    def mime_coherent_with_tipo(self):
        if self.mime_type is None:
            return self
        low = self.mime_type.lower()
        if self.tipo == TipoEvidenciaSolicitudEnum.FOTO and not low.startswith("image/"):
            raise ValueError("Para FOTO, mime_type debe empezar por image/")
        if self.tipo == TipoEvidenciaSolicitudEnum.AUDIO and not low.startswith("audio/"):
            raise ValueError("Para AUDIO, mime_type debe empezar por audio/")
        return self


class SolicitudUbicacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    latitud: Decimal
    longitud: Decimal
    precision_metros: Decimal | None
    direccion_referencia: str | None
    es_actual: bool
    registrado_at: datetime


class SolicitudEvidenciaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    tipo: TipoEvidenciaSolicitudEnum
    archivo_url: str
    mime_type: str | None
    nombre_archivo: str | None
    tamano_bytes: int | None
    created_at: datetime


class SolicitudEmergenciaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    vehiculo_id: int
    estado: EstadoSolicitudSeguimientoEnum
    descripcion_texto: str | None
    ai_payload: dict | None = None
    created_at: datetime
    updated_at: datetime
    taller_id: int | None = None
    tecnico_id: int | None = None
    tiempo_estimado_min: int | None = None
    finalizada_at: datetime | None = None
    tecnico_asignado_at: datetime | None = None
    tecnico_ult_latitud: Decimal | None = None
    tecnico_ult_longitud: Decimal | None = None
    tecnico_ult_precision_metros: Decimal | None = None
    tecnico_ult_ubicacion_at: datetime | None = None
    presupuesto_bob: Decimal | None = Field(
        default=None,
        description="Monto en bolivianos (BOB) informado por el técnico al iniciar atención en sitio.",
    )
    presupuesto_registrado_at: datetime | None = Field(
        default=None,
        description="Momento en que el técnico registró el presupuesto.",
    )


class UbicacionTecnicoCompartidaRead(BaseModel):
    """Última posición compartida por el técnico en la solicitud (lectura cliente o confirmación POST)."""

    solicitud_id: int
    latitud: Decimal
    longitud: Decimal
    precision_metros: Decimal | None = None
    actualizado_at: datetime


class SolicitudEmergenciaDetailRead(SolicitudEmergenciaRead):
    ubicaciones: list[SolicitudUbicacionRead]
    evidencias: list[SolicitudEvidenciaRead]


class TallerSeguimientoRead(BaseModel):
    """CU17 — datos mínimos del taller asignado (solo lectura cliente)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_comercial: str
    telefono_contacto: str
    email_contacto: str
    direccion: str
    ciudad: str


class TecnicoSeguimientoRead(BaseModel):
    """Técnico asignado (CU17 ext.) — nombre desde usuario vinculado."""

    id: int
    nombres: str
    apellidos: str
    telefono: str


class SolicitudHistorialEstadoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado_anterior: EstadoSolicitudSeguimientoEnum | None
    estado_nuevo: EstadoSolicitudSeguimientoEnum
    observacion: str | None
    created_at: datetime


class SolicitudSeguimientoRead(BaseModel):
    """CU16 + CU17 + CU18 — agregado de consulta de seguimiento para el cliente."""

    solicitud_id: int
    estado: EstadoSolicitudSeguimientoEnum
    updated_at: datetime
    ai_payload: dict | None = Field(
        None,
        description="Resultado del pipeline IA tras crear la solicitud (version, clasificacion, prioridad, resumen, etc.).",
    )
    tiempo_estimado_min: int | None = Field(
        None,
        description="CU18: minutos estimados hasta llegada (mantenido por taller/sistema).",
    )
    finalizada_at: datetime | None = None
    taller: TallerSeguimientoRead | None = None
    tecnico: TecnicoSeguimientoRead | None = None
    historial_estados: list[SolicitudHistorialEstadoRead]
    tiene_ubicacion_cliente: bool = Field(
        default=False,
        description="Indica si ya hay al menos un punto de ubicación registrado en la solicitud.",
    )
    tiene_evidencia_foto: bool = Field(
        default=False,
        description="Indica si hay al menos una evidencia de tipo FOTO almacenada.",
    )
    tiene_evidencia_audio: bool = Field(
        default=False,
        description="Indica si hay al menos una evidencia de tipo AUDIO almacenada.",
    )
    presupuesto_bob: Decimal | None = Field(
        default=None,
        description="Monto en bolivianos (BOB) informado por el técnico al iniciar atención en sitio.",
    )
    presupuesto_registrado_at: datetime | None = Field(
        default=None,
        description="Momento en que el técnico registró el presupuesto.",
    )
