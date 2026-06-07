# ORM — Ciclo 4: SincronizacionOffline, ErrorSincronizacion
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SincronizacionOffline(Base):
    """
    Tabla: sincronizacion_offline
    Cola de entidades capturadas sin conexión.

    Anti-duplicado: UNIQUE (tenant_id, client_uuid) garantiza que la misma
    captura local nunca se registre dos veces aunque el cliente reintente.

    estado_local: pendiente → enviado → sincronizado | error
    """
    __tablename__ = "sincronizacion_offline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # Tipo de entidad: 'incidente', 'evento', 'pago', …
    entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    # UUID generado en el dispositivo — clave del anti-duplicado
    client_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Datos crudos capturados sin internet
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    estado_local: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(Text)
    # Se llena cuando se sincroniza correctamente con el backend
    incidente_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidentes.id", ondelete="SET NULL")
    )
    registrado_local_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sincronizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    errores: Mapped[list["ErrorSincronizacion"]] = relationship(
        back_populates="sincronizacion",
        cascade="all, delete-orphan",
    )


class ErrorSincronizacion(Base):
    """
    Tabla: errores_sincronizacion
    Log de cada intento fallido de sincronización.
    Permite diagnosticar patrones de error por usuario/tenant.
    """
    __tablename__ = "errores_sincronizacion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    sincronizacion_id: Mapped[int] = mapped_column(
        ForeignKey("sincronizacion_offline.id", ondelete="CASCADE"), nullable=False
    )
    intento_num: Mapped[int] = mapped_column(Integer, nullable=False)
    codigo_error: Mapped[str | None] = mapped_column(String(60))
    detalle: Mapped[str | None] = mapped_column(Text)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sincronizacion: Mapped["SincronizacionOffline"] = relationship(back_populates="errores")
