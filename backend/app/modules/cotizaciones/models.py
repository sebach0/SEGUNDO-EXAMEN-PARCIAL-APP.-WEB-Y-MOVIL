# ORM — cotizaciones y cotizacion_items
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoCotizacionEnum(str, enum.Enum):
    ENVIADA   = "ENVIADA"
    ACEPTADA  = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    EXPIRADA  = "EXPIRADA"


_estado_cot_sa = SAEnum(EstadoCotizacionEnum, name="estado_cotizacion")


class Cotizacion(Base):
    """
    Tabla: cotizaciones
    Propuesta formal de un taller para atender una solicitud de emergencia.
    Un taller solo puede enviar una cotización por solicitud (UNIQUE solicitud_id + taller_id).
    Cuando el cliente selecciona una, las demás pasan a EXPIRADA.
    """
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="RESTRICT"), nullable=False
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[EstadoCotizacionEnum] = mapped_column(
        _estado_cot_sa, nullable=False, default=EstadoCotizacionEnum.ENVIADA
    )
    descripcion_danio: Mapped[str] = mapped_column(Text, nullable=False)
    detalle_servicio: Mapped[str] = mapped_column(Text, nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tiempo_estimado_llegada_min: Mapped[int | None] = mapped_column(Integer)
    tiempo_estimado_reparacion_min: Mapped[int | None] = mapped_column(Integer)
    incluye_grua: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    garantia_descripcion: Mapped[str | None] = mapped_column(Text)
    comentarios: Mapped[str | None] = mapped_column(Text)
    distancia_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    servicios_ofrecidos: Mapped[list | None] = mapped_column(JSON)
    seleccionada_at: Mapped[datetime | None] = mapped_column(DateTime)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    creado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    actualizado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    items: Mapped[list["CotizacionItem"]] = relationship(
        back_populates="cotizacion", cascade="all, delete-orphan"
    )


class CotizacionItem(Base):
    """
    Tabla: cotizacion_items
    Líneas de detalle de una cotización (repuestos, mano de obra, etc.)
    """
    __tablename__ = "cotizacion_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(
        ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    cotizacion: Mapped["Cotizacion"] = relationship(back_populates="items")

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario
