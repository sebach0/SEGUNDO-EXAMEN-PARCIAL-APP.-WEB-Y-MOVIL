from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, MetodoPagoEnum


class PagoSolicitudCreateIn(BaseModel):
    """CU20 — alta de cobro (monto informado por cliente en esta fase; idealmente vendrá de tarifario)."""

    monto: Decimal = Field(..., gt=0, description="Monto positivo (2 decimales recomendados).")
    metodo: MetodoPagoEnum
    moneda: str = Field(default="BOB", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")

    @field_validator("moneda")
    @classmethod
    def moneda_mayus(cls, v: str) -> str:
        return v.strip().upper()


class PagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    cliente_id: int
    tenant_id: int | None = None
    cotizacion_id: int | None = None
    monto: Decimal
    moneda: str
    metodo: MetodoPagoEnum
    estado: EstadoPagoEnum
    referencia_externa: str | None
    proveedor: str
    metadata_json: dict | None
    conciliado_at: datetime | None
    created_at: datetime
    pagado_at: datetime | None


class PagoIniciadoRead(PagoRead):
    """Respuesta de ``POST .../pagos`` cuando la pasarela devuelve datos extra (Stripe PaymentSheet)."""

    stripe_client_secret: str | None = None
    stripe_publishable_key: str | None = None


class PagoStripeConfirmIn(BaseModel):
    """Confirmación tras éxito en el SDK móvil (o webhook futuro)."""

    payment_intent_id: str | None = Field(
        default=None,
        description="Si se omite, se usa ``referencia_externa`` del pago (PaymentIntent id).",
    )


class PagoValidateManualIn(BaseModel):
    """Admin valida pago manual (transferencia / efectivo)."""

    aprobado: bool = True
    observacion: str | None = Field(default=None, max_length=500)


class AdminPagoListRead(BaseModel):
    items: list[PagoRead]
    total: int
