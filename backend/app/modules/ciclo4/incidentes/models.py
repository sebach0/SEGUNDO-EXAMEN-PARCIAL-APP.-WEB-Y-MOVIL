# ORM — Ciclo 4: Incidente, TipoIncidente, Zona, IncidenteTaller,
#                IncidenteEstadoHistorial, IncidenteTracking, EventoTiempoReal
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── ENUMs ────────────────────────────────────────────────────────────────────

class EstadoIncidenteEnum(str, enum.Enum):
    """
    Ciclo de vida del incidente Ciclo 4.
    Diferente del EstadoSolicitudSeguimientoEnum (Ciclo 1-3).
    """
    PENDIENTE       = "PENDIENTE"
    BUSCANDO_TALLER = "BUSCANDO_TALLER"
    TALLER_ASIGNADO = "TALLER_ASIGNADO"
    EN_CAMINO       = "EN_CAMINO"
    EN_ATENCION     = "EN_ATENCION"
    FINALIZADO      = "FINALIZADO"
    CANCELADO       = "CANCELADO"


class SyncEstadoEnum(str, enum.Enum):
    """Estado de sincronización offline del incidente."""
    PENDIENTE    = "pendiente"
    ENVIADO      = "enviado"
    SINCRONIZADO = "sincronizado"
    ERROR        = "error"


class OrigenIncidenteEnum(str, enum.Enum):
    ONLINE  = "ONLINE"
    OFFLINE = "OFFLINE"


class EstadoIncidenteTallerEnum(str, enum.Enum):
    OFRECIDO    = "OFRECIDO"
    ACEPTADO    = "ACEPTADO"
    RECHAZADO   = "RECHAZADO"
    SELECCIONADO = "SELECCIONADO"
    CANCELADO   = "CANCELADO"


def _pg_enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """PostgreSQL recibe el .value del enum Python, no el .name (ej. sincronizado, no SINCRONIZADO)."""
    return [member.value for member in enum_cls]


_estado_incidente_sa = SAEnum(
    EstadoIncidenteEnum,
    name="estado_incidente_v2",
    values_callable=_pg_enum_values,
    create_type=False,
)
_sync_estado_sa = SAEnum(
    SyncEstadoEnum,
    name="sync_estado_incidente",
    values_callable=_pg_enum_values,
    create_type=False,
)
_origen_sa = SAEnum(
    OrigenIncidenteEnum,
    name="origen_incidente",
    values_callable=_pg_enum_values,
    create_type=False,
)
_estado_inc_taller_sa = SAEnum(
    EstadoIncidenteTallerEnum,
    name="estado_incidente_taller",
    values_callable=_pg_enum_values,
    create_type=False,
)


# ── Catálogos ────────────────────────────────────────────────────────────────

class TipoIncidente(Base):
    """
    Tabla: tipos_incidente
    Catálogo global (BATERIA, LLANTA, MOTOR, CHOQUE, OTROS).
    Base del KPI "incidentes por tipo".
    """
    __tablename__ = "tipos_incidente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(150))


class Zona(Base):
    """
    Tabla: zonas
    Zona geográfica por tenant. Base del KPI "zonas con más incidentes".
    """
    __tablename__ = "zonas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(100))


# ── Incidente ────────────────────────────────────────────────────────────────

class Incidente(Base):
    """
    Tabla: incidentes
    Núcleo de Ciclo 4.  Diferente de solicitudes_emergencia (Ciclo 1-3).

    Campos clave:
    - tenant_id:  aislamiento multi-tenant (NUNCA devolver datos de otro tenant).
    - client_uuid: ID generado en el dispositivo para anti-duplicado offline.
    - sync_estado: estado local de sincronización.
    - origen:      ONLINE | OFFLINE.
    - timestamps de ciclo de vida: base de todos los KPIs de tiempo.
    """
    __tablename__ = "incidentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="RESTRICT"), nullable=False
    )
    tipo_incidente_id: Mapped[int | None] = mapped_column(
        ForeignKey("tipos_incidente.id", ondelete="RESTRICT")
    )
    zona_id: Mapped[int | None] = mapped_column(
        ForeignKey("zonas.id", ondelete="RESTRICT")
    )
    taller_asignado_id: Mapped[int | None] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT")
    )

    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[EstadoIncidenteEnum] = mapped_column(
        _estado_incidente_sa, nullable=False, default=EstadoIncidenteEnum.PENDIENTE
    )
    prioridad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")

    # Geolocalización
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    direccion_referencia: Mapped[str | None] = mapped_column(String(255))

    # SLA en minutos (reporte → atención); base para KPI cumplimiento SLA
    sla_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # Soporte offline / sincronización
    origen: Mapped[OrigenIncidenteEnum] = mapped_column(
        _origen_sa, nullable=False, default=OrigenIncidenteEnum.ONLINE
    )
    client_uuid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    sync_estado: Mapped[SyncEstadoEnum] = mapped_column(
        _sync_estado_sa, nullable=False, default=SyncEstadoEnum.SINCRONIZADO
    )

    # Timestamps del ciclo de vida  (base de TODOS los KPIs de tiempo)
    reportado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    buscando_taller_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    asignado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    en_camino_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    en_atencion_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(255))

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relaciones
    tipo_incidente: Mapped["TipoIncidente | None"] = relationship()
    historial_estados: Mapped[list["IncidenteEstadoHistorial"]] = relationship(
        back_populates="incidente",
        cascade="all, delete-orphan",
        order_by="IncidenteEstadoHistorial.creado_en",
    )
    tracking_records: Mapped[list["IncidenteTracking"]] = relationship(
        back_populates="incidente",
        cascade="all, delete-orphan",
    )
    eventos: Mapped[list["EventoTiempoReal"]] = relationship(
        back_populates="incidente",
        cascade="all, delete-orphan",
    )
    asignaciones_taller: Mapped[list["IncidenteTaller"]] = relationship(
        back_populates="incidente",
        cascade="all, delete-orphan",
    )


# ── Asignación taller ↔ incidente ────────────────────────────────────────────

class IncidenteTaller(Base):
    """
    Tabla: incidente_taller
    Registro de ofertas y respuestas (acepta/rechaza) por taller.
    Base del KPI "talleres más eficientes" (tiempo de respuesta).
    """
    __tablename__ = "incidente_taller"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    incidente_id: Mapped[int] = mapped_column(
        ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[EstadoIncidenteTallerEnum] = mapped_column(
        _estado_inc_taller_sa, nullable=False, default=EstadoIncidenteTallerEnum.OFRECIDO
    )
    distancia_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    ofrecido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    respondido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_rechazo: Mapped[str | None] = mapped_column(String(255))

    incidente: Mapped["Incidente"] = relationship(back_populates="asignaciones_taller")


# ── Historial de estados ──────────────────────────────────────────────────────

class IncidenteEstadoHistorial(Base):
    """
    Tabla: incidente_estado_historial
    Auditoría de cada transición de estado. Inmutable (no se edita).
    Cada cambio de estado genera una fila aquí + un EventoTiempoReal.
    """
    __tablename__ = "incidente_estado_historial"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    incidente_id: Mapped[int] = mapped_column(
        ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(30))
    estado_nuevo: Mapped[str] = mapped_column(String(30), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    comentario: Mapped[str | None] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    incidente: Mapped["Incidente"] = relationship(back_populates="historial_estados")


# ── Tracking GPS ─────────────────────────────────────────────────────────────

class IncidenteTracking(Base):
    """
    Tabla: incidente_tracking
    Registro de posiciones GPS del técnico durante la atención.
    Cada punto se emite también como EventoTiempoReal tipo TRACKING_UPDATE.
    """
    __tablename__ = "incidente_tracking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    incidente_id: Mapped[int] = mapped_column(
        ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    taller_id: Mapped[int | None] = mapped_column(
        ForeignKey("talleres.id", ondelete="SET NULL")
    )
    tecnico_id: Mapped[int | None] = mapped_column(
        ForeignKey("tecnicos.id", ondelete="SET NULL")
    )
    latitud: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitud: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    velocidad_kmh: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    incidente: Mapped["Incidente"] = relationship(back_populates="tracking_records")


# ── Eventos tiempo real ───────────────────────────────────────────────────────

class EventoTiempoReal(Base):
    """
    Tabla: eventos_tiempo_real
    Log persistente de todos los eventos emitidos por WebSocket.
    Permite recuperar el historial de eventos aunque el cliente no estuviera conectado.

    tipo_evento: ESTADO_CAMBIADO | TRACKING_UPDATE | TALLER_ACEPTO |
                 TALLER_RECHAZO | AUXILIO_EN_CAMINO | SERVICIO_ATENDIDO |
                 SERVICIO_FINALIZADO
    canal:       "incidente:123" | "tenant:5"
    """
    __tablename__ = "eventos_tiempo_real"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    incidente_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidentes.id", ondelete="CASCADE")
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    canal: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_evento: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    emitido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    incidente: Mapped["Incidente | None"] = relationship(back_populates="eventos")
