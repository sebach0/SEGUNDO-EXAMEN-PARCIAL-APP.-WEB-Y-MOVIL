# ORM — tabla pagos (enums alineados con PostgreSQL).
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EstadoPagoEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    FALLIDO = "FALLIDO"
    ANULADO = "ANULADO"


class MetodoPagoEnum(str, enum.Enum):
    QR = "QR"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    EFECTIVO = "EFECTIVO"
    OTRO = "OTRO"


class ResponsablePagoEnum(str, enum.Enum):
    CLIENTE = "CLIENTE"
    SEGURO  = "SEGURO"
    MIXTO   = "MIXTO"


_estado_pago_sa = SAEnum(EstadoPagoEnum, name="estado_pago")
_metodo_pago_sa = SAEnum(MetodoPagoEnum, name="metodo_pago")
_responsable_pago_sa = SAEnum(ResponsablePagoEnum, name="responsable_pago")


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="RESTRICT"), nullable=False
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="BOB")
    metodo: Mapped[MetodoPagoEnum] = mapped_column(_metodo_pago_sa, nullable=False)
    estado: Mapped[EstadoPagoEnum] = mapped_column(_estado_pago_sa, nullable=False, default=EstadoPagoEnum.PENDIENTE)
    referencia_externa: Mapped[str | None] = mapped_column(String(255))
    proveedor: Mapped[str] = mapped_column(String(32), nullable=False, default="SIMULADO")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata_json", JSONB)
    conciliado_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pagado_at: Mapped[datetime | None] = mapped_column(DateTime)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    cotizacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("cotizaciones.id", ondelete="SET NULL"), nullable=True
    )
    # ── Responsable de pago / seguro ──────────────────────────────────────────
    responsable_pago: Mapped[ResponsablePagoEnum] = mapped_column(
        _responsable_pago_sa, nullable=False, default=ResponsablePagoEnum.CLIENTE
    )
    monto_seguro: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    numero_poliza: Mapped[str | None] = mapped_column(String(100))
    aseguradora: Mapped[str | None] = mapped_column(String(150))
