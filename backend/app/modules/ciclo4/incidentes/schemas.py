# Schemas Pydantic — Ciclo 4: Incidentes, Tracking, Eventos, Historial
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.modules.ciclo4.incidentes.models import (
    EstadoIncidenteEnum,
    EstadoIncidenteTallerEnum,
    OrigenIncidenteEnum,
    SyncEstadoEnum,
)


# ── Catálogos ─────────────────────────────────────────────────────────────────

class TipoIncidenteRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    nombre: str
    descripcion: str | None = None


class ZonaRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    tenant_id: int
    nombre: str
    ciudad: str | None = None


# ── Incidente — entrada ───────────────────────────────────────────────────────

class IncidenteCreateIn(BaseModel):
    """
    Cuerpo para crear un incidente.
    client_uuid es OBLIGATORIO cuando origen=OFFLINE (anti-duplicado).
    """
    vehiculo_id: int
    descripcion: str | None = None
    tipo_incidente_id: int | None = None
    zona_id: int | None = None
    prioridad: str = Field("MEDIA", pattern=r"^(BAJA|MEDIA|ALTA|CRITICA)$")
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    direccion_referencia: str | None = Field(None, max_length=255)
    sla_minutos: int = Field(60, ge=5, le=1440)
    origen: OrigenIncidenteEnum = OrigenIncidenteEnum.ONLINE
    client_uuid: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_uuid_for_offline(self) -> "IncidenteCreateIn":
        if self.origen == OrigenIncidenteEnum.OFFLINE and self.client_uuid is None:
            raise ValueError("client_uuid es obligatorio para incidentes OFFLINE")
        return self


class CambiarEstadoIn(BaseModel):
    nuevo_estado: EstadoIncidenteEnum
    comentario: str | None = Field(None, max_length=255)
    motivo_cancelacion: str | None = Field(None, max_length=255)


# ── Tracking ──────────────────────────────────────────────────────────────────

class TrackingCreateIn(BaseModel):
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)
    velocidad_kmh: Decimal | None = Field(None, ge=0)


class TrackingRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    incidente_id: int
    taller_id: int | None = None
    tecnico_id: int | None = None
    latitud: Decimal
    longitud: Decimal
    velocidad_kmh: Decimal | None = None
    registrado_en: datetime


# ── Historial de estado ────────────────────────────────────────────────────────

class HistorialEstadoRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    estado_anterior: str | None = None
    estado_nuevo: str
    usuario_id: int | None = None
    comentario: str | None = None
    creado_en: datetime


# ── Evento tiempo real ─────────────────────────────────────────────────────────

class EventoTiempoRealRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    canal: str
    tipo_evento: str
    payload: dict[str, Any] | None = None
    emitido_en: datetime


# ── Incidente — respuesta ─────────────────────────────────────────────────────

class IncidenteRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    tenant_id: int
    cliente_id: int
    vehiculo_id: int
    tipo_incidente_id: int | None = None
    zona_id: int | None = None
    taller_asignado_id: int | None = None
    descripcion: str | None = None
    estado: EstadoIncidenteEnum
    prioridad: str
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    direccion_referencia: str | None = None
    sla_minutos: int
    origen: OrigenIncidenteEnum
    client_uuid: uuid.UUID | None = None
    sync_estado: SyncEstadoEnum
    reportado_en: datetime
    buscando_taller_en: datetime | None = None
    asignado_en: datetime | None = None
    en_camino_en: datetime | None = None
    en_atencion_en: datetime | None = None
    finalizado_en: datetime | None = None
    cancelado_en: datetime | None = None
    motivo_cancelacion: str | None = None
    creado_en: datetime
    actualizado_en: datetime


class IncidenteDetalleRead(IncidenteRead):
    """Respuesta completa con historial, tracking y eventos recientes."""
    historial_estados: list[HistorialEstadoRead] = []
    tracking_reciente: list[TrackingRead] = []
    eventos_recientes: list[EventoTiempoRealRead] = []


# ── WebSocket — formato de mensajes ──────────────────────────────────────────

class WsEventoOut(BaseModel):
    """Formato JSON que se envía por WebSocket a clientes conectados."""
    type: str                           # ESTADO_CAMBIADO, TRACKING_UPDATE, …
    incident_id: int
    status: str | None = None           # estado actual del incidente
    message: str | None = None
    payload: dict[str, Any] = {}
    emitted_at: str                     # ISO 8601
