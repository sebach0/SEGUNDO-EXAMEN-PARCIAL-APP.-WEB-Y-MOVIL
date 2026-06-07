from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.cotizaciones.models import EstadoCotizacionEnum


# ── Items de cotización ───────────────────────────────────────────────────────

class CotizacionItemIn(BaseModel):
    descripcion: str = Field(min_length=1, max_length=255)
    cantidad: Decimal = Field(gt=0, default=1)
    precio_unitario: Decimal = Field(ge=0)


class CotizacionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cotizacion_id: int
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal


class ServicioOfrecidoRead(BaseModel):
    id: int
    nombre: str
    codigo: str


class CotizacionContextoRead(BaseModel):
    """Contexto para que el taller arme su oferta (distancia + servicios del taller)."""
    distancia_km: Decimal | None = None
    tarifa_traslado_bs_km: Decimal = Decimal("5")
    costo_traslado_estimado: Decimal | None = None
    servicios_disponibles: list[ServicioOfrecidoRead] = Field(default_factory=list)
    tiene_grua: bool = False
    cotizacion_activa: bool = False
    taller_tiene_ubicacion: bool = False
    taller_lat: Decimal | None = None
    taller_lng: Decimal | None = None
    incidente_lat: Decimal | None = None
    incidente_lng: Decimal | None = None
    eta_sugerida_min: int | None = None


# ── Crear cotización ──────────────────────────────────────────────────────────

class CotizacionCreateIn(BaseModel):
    descripcion_danio: str = Field(min_length=5, max_length=2000)
    detalle_servicio: str = Field(min_length=5, max_length=2000)
    monto_total: Decimal = Field(gt=0)
    tiempo_estimado_llegada_min: int | None = Field(default=None, ge=1, le=10080)
    tiempo_estimado_reparacion_min: int | None = Field(default=None, ge=1, le=100000)
    incluye_grua: bool = False
    garantia_descripcion: str | None = Field(default=None, max_length=2000)
    comentarios: str | None = Field(default=None, max_length=2000)
    items: list[CotizacionItemIn] = Field(default_factory=list)


# ── Lectura de cotización ─────────────────────────────────────────────────────

class CotizacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    taller_id: int
    tenant_id: int | None = None
    taller_nombre: str | None = None
    estado: EstadoCotizacionEnum
    descripcion_danio: str
    detalle_servicio: str
    monto_total: Decimal
    tiempo_estimado_llegada_min: int | None
    tiempo_estimado_reparacion_min: int | None
    incluye_grua: bool
    garantia_descripcion: str | None
    comentarios: str | None
    distancia_km: Decimal | None = None
    servicios_ofrecidos: list[ServicioOfrecidoRead] = Field(default_factory=list)
    seleccionada_at: datetime | None
    creado_at: datetime
    actualizado_at: datetime
    items: list[CotizacionItemRead] = Field(default_factory=list)


class CotizacionRespondIn(BaseModel):
    """CU48 — aprobar (ACEPTADA) o rechazar (RECHAZADA) cotización."""
    decision: str = Field(..., pattern=r"^(APROBADA|RECHAZADA|ACEPTADA)$")
    comment: str | None = Field(default=None, max_length=2000)


class CotizacionRechazarIn(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)
