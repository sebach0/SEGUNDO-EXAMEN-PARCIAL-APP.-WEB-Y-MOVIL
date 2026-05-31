# Tablas ciclo 3 taller — scripts 006 (bandeja), 007 (asignación), 009 (comisiones)
from __future__ import annotations

import enum
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EstadoBandejaTallerEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    EXPIRADA = "EXPIRADA"


_estado_bandeja_sa = SAEnum(EstadoBandejaTallerEnum, name="estado_bandeja_taller")


class TallerDisponibilidad(Base):
    """Una fila por taller (taller_id UNIQUE)."""

    __tablename__ = "taller_disponibilidad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    acepta_nuevas_solicitudes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    capacidad_maxima_diaria: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    servicios_activos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    observacion: Mapped[str | None] = mapped_column(Text)
    updated_by_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SolicitudTallerBandeja(Base):
    """Bandeja por (solicitud_id, taller_id)."""

    __tablename__ = "solicitud_taller_bandeja"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    estado: Mapped[EstadoBandejaTallerEnum] = mapped_column(
        _estado_bandeja_sa,
        nullable=False,
        default=EstadoBandejaTallerEnum.PENDIENTE,
    )
    motivo_rechazo: Mapped[str | None] = mapped_column(Text)
    creado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    respondido_at: Mapped[datetime | None] = mapped_column(DateTime)


class EstadoAsignacionTecnicoEnum(str, enum.Enum):
    """scripts/007_fase2_asignacion_tecnico.sql"""

    ASIGNADO = "ASIGNADO"
    REASIGNADO = "REASIGNADO"
    CANCELADO = "CANCELADO"


_estado_asignacion_tecnico_sa = SAEnum(EstadoAsignacionTecnicoEnum, name="estado_asignacion_tecnico")


class SolicitudAsignacionTecnico(Base):
    """Historial de asignaciones de técnico a una solicitud (CU28)."""

    __tablename__ = "solicitud_asignaciones_tecnico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    tecnico_id: Mapped[int] = mapped_column(
        ForeignKey("tecnicos.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    estado: Mapped[EstadoAsignacionTecnicoEnum] = mapped_column(
        _estado_asignacion_tecnico_sa,
        nullable=False,
        default=EstadoAsignacionTecnicoEnum.ASIGNADO,
    )
    asignado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    observacion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class EstadoComisionTallerEnum(str, enum.Enum):
    """scripts/009_fase4_historial_comisiones.sql"""

    PENDIENTE = "PENDIENTE"
    CALCULADA = "CALCULADA"
    LIQUIDADA = "LIQUIDADA"
    ANULADA = "ANULADA"


_estado_comision_sa = SAEnum(EstadoComisionTallerEnum, name="estado_comision_taller")


class ComisionTaller(Base):
    """Comisión por solicitud pagada (CU31)."""

    __tablename__ = "comisiones_taller"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    pago_id: Mapped[int | None] = mapped_column(
        ForeignKey("pagos.id", onupdate="CASCADE", ondelete="SET NULL"),
        unique=True,
    )
    porcentaje_plataforma: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("10.00"))
    monto_servicio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_comision: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_taller_neto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[EstadoComisionTallerEnum] = mapped_column(
        _estado_comision_sa,
        nullable=False,
        default=EstadoComisionTallerEnum.PENDIENTE,
    )
    calculado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    liquidado_at: Mapped[datetime | None] = mapped_column(DateTime)
