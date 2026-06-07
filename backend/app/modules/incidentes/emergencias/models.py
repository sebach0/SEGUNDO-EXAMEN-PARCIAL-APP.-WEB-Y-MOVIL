# Modelos: solicitudes_emergencia, solicitud_ubicaciones, solicitud_evidencias, historial estado (fase 2).
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoSolicitudSeguimientoEnum(str, enum.Enum):
    """CU16 — estados extendidos (fase 2); compatibles con valores de fase 1."""

    REGISTRADA = "REGISTRADA"
    EN_REVISION = "EN_REVISION"
    TALLER_ASIGNADO = "TALLER_ASIGNADO"
    TECNICO_ASIGNADO = "TECNICO_ASIGNADO"
    EN_CAMINO = "EN_CAMINO"
    EN_ATENCION = "EN_ATENCION"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class TipoEvidenciaSolicitudEnum(str, enum.Enum):
    FOTO = "FOTO"
    AUDIO = "AUDIO"


class CancelacionFaseEnum(str, enum.Enum):
    PRE_ASIGNACION = "PRE_ASIGNACION"
    POST_ASIGNACION = "POST_ASIGNACION"
    EN_CAMINO = "EN_CAMINO"
    EN_ATENCION = "EN_ATENCION"


class EtaOrigenEnum(str, enum.Enum):
    MANUAL = "MANUAL"
    FALLBACK = "FALLBACK"
    COTIZACION = "COTIZACION"
    GPS = "GPS"


class SyncEstadoSolicitudEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    SINCRONIZADO = "SINCRONIZADO"
    ERROR = "ERROR"


_estado_seguimiento_sa = SAEnum(
    EstadoSolicitudSeguimientoEnum,
    name="estado_solicitud_seguimiento",
)


class SolicitudEmergencia(Base):
    """CU11 cabecera; fase 2: asignación taller/técnico, ETA, historial."""

    __tablename__ = "solicitudes_emergencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[EstadoSolicitudSeguimientoEnum] = mapped_column(_estado_seguimiento_sa, nullable=False)
    descripcion_texto: Mapped[str | None] = mapped_column(Text)
    ai_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    taller_id: Mapped[int | None] = mapped_column(ForeignKey("talleres.id", ondelete="SET NULL"))
    tecnico_id: Mapped[int | None] = mapped_column(ForeignKey("tecnicos.id", ondelete="SET NULL"))
    tiempo_estimado_min: Mapped[int | None] = mapped_column(Integer)
    finalizada_at: Mapped[datetime | None] = mapped_column(DateTime)
    tecnico_asignado_at: Mapped[datetime | None] = mapped_column(DateTime)

    tecnico_ult_latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    tecnico_ult_longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    tecnico_ult_precision_metros: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    tecnico_ult_ubicacion_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    presupuesto_bob: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    presupuesto_registrado_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    cancelacion_fase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    taller_habia_llegado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    reportado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    asignado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    en_camino_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    en_atencion_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    llegada_real_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    eta_actualizado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    eta_origen: Mapped[str | None] = mapped_column(String(20), nullable=True)
    retraso_notificado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_uuid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    sync_estado: Mapped[str] = mapped_column(String(20), nullable=False, default="SINCRONIZADO")
    zona_id: Mapped[int | None] = mapped_column(
        ForeignKey("zonas.id", ondelete="SET NULL"), nullable=True
    )

    ubicaciones: Mapped[list["SolicitudUbicacion"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
    )
    evidencias: Mapped[list["SolicitudEvidencia"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
    )
    historial_estados: Mapped[list["SolicitudHistorialEstado"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
        order_by="SolicitudHistorialEstado.created_at",
    )
    taller: Mapped["Taller | None"] = relationship("Taller", foreign_keys=[taller_id])
    tecnico: Mapped["Tecnico | None"] = relationship("Tecnico", foreign_keys=[tecnico_id])


class SolicitudHistorialEstado(Base):
    """Auditoría de transiciones de estado (CU16); actor taller/sistema en fases posteriores."""

    __tablename__ = "solicitud_historial_estado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="CASCADE"), nullable=False
    )
    estado_anterior: Mapped[EstadoSolicitudSeguimientoEnum | None] = mapped_column(_estado_seguimiento_sa)
    estado_nuevo: Mapped[EstadoSolicitudSeguimientoEnum] = mapped_column(
        _estado_seguimiento_sa,
        nullable=False,
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    observacion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    solicitud: Mapped["SolicitudEmergencia"] = relationship(back_populates="historial_estados")


class SolicitudUbicacion(Base):
    """CU12: puntos de ubicación; a lo sumo uno con es_actual = TRUE por solicitud."""

    __tablename__ = "solicitud_ubicaciones"
    __table_args__ = (
        Index(
            "uq_solicitud_ubicacion_actual",
            "solicitud_id",
            unique=True,
            postgresql_where=text("es_actual = true"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="CASCADE"), nullable=False
    )
    latitud: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitud: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    precision_metros: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    direccion_referencia: Mapped[str | None] = mapped_column(Text)
    es_actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registrado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    solicitud: Mapped["SolicitudEmergencia"] = relationship(back_populates="ubicaciones")


class SolicitudEvidencia(Base):
    """CU13 (FOTO) / CU14 (AUDIO): referencia a archivo (URL); almacenamiento externo en fase 1."""

    __tablename__ = "solicitud_evidencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoEvidenciaSolicitudEnum] = mapped_column(
        SAEnum(TipoEvidenciaSolicitudEnum, name="tipo_evidencia_solicitud"),
        nullable=False,
    )
    archivo_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    nombre_archivo: Mapped[str | None] = mapped_column(String(255))
    tamano_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    solicitud: Mapped["SolicitudEmergencia"] = relationship(back_populates="evidencias")
