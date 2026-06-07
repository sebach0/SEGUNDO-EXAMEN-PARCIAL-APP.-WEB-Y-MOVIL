# Schemas Pydantic — Ciclo 4: Sincronización Offline (CU38-CU42)
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.ciclo4.incidentes.schemas import IncidenteCreateIn


# ── CU39 / CU38 — Sincronizar incidente offline (móvil) ─────────────────────

class SyncIncidenteIn(BaseModel):
    """
    Payload que llega desde la app móvil para sincronizar un incidente OFFLINE.
    Internamente es igual a IncidenteCreateIn pero SIEMPRE incluye client_uuid.
    """
    client_uuid: uuid.UUID
    vehiculo_id: int
    descripcion: str | None = None
    tipo_incidente_id: int | None = None
    zona_id: int | None = None
    prioridad: str = Field("MEDIA", pattern=r"^(BAJA|MEDIA|ALTA|CRITICA)$")
    latitud: float | None = None
    longitud: float | None = None
    direccion_referencia: str | None = Field(None, max_length=255)
    sla_minutos: int = Field(60, ge=5, le=1440)
    registrado_local_en: datetime | None = None


class SyncIncidenteResultado(BaseModel):
    """Respuesta tras sincronizar un incidente offline."""
    client_uuid: uuid.UUID
    incidente_id: int
    creado_nuevo: bool       # True si se creó; False si ya existía (anti-duplicado)
    estado: str
    mensaje: str


# ── CU40 — Estado de sincronización ──────────────────────────────────────────

class SyncStatusItemRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    entidad: str
    client_uuid: uuid.UUID
    estado_local: str
    intentos: int
    ultimo_error: str | None = None
    incidente_id: int | None = None
    registrado_local_en: datetime | None = None
    sincronizado_en: datetime | None = None
    creado_en: datetime


# ── CU41 / CU42 — Sincronizar eventos web (Angular PWA) ──────────────────────

class WebEventoIn(BaseModel):
    """
    Evento capturado offline por Angular PWA (actualización de estado,
    aceptación/rechazo de incidente, etc.).
    """
    client_uuid: uuid.UUID
    incidente_id: int
    tipo_evento: str = Field(
        ...,
        description="ESTADO_CAMBIADO | TALLER_ACEPTO | TALLER_RECHAZO | …",
    )
    payload: dict[str, Any] = {}
    registrado_local_en: datetime | None = None


class WebSyncIn(BaseModel):
    eventos: list[WebEventoIn] = Field(..., min_length=1)


class WebEventoResultado(BaseModel):
    client_uuid: uuid.UUID
    incidente_id: int
    tipo_evento: str
    sincronizado: bool
    error: str | None = None


class WebSyncResultado(BaseModel):
    total: int
    sincronizados: int
    con_error: int
    detalle: list[WebEventoResultado]
