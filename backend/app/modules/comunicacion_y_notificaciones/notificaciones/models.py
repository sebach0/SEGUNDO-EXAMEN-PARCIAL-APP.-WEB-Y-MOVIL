from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoNotificacionEnum(str, enum.Enum):
    SOLICITUD_CREADA = "SOLICITUD_CREADA"
    ESTADO_ACTUALIZADO = "ESTADO_ACTUALIZADO"
    TALLER_ASIGNADO = "TALLER_ASIGNADO"
    TECNICO_ASIGNADO = "TECNICO_ASIGNADO"
    MENSAJE_NUEVO = "MENSAJE_NUEVO"


_tipo_notif_sa = SAEnum(TipoNotificacionEnum, name="tipo_notificacion")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    solicitud_id: Mapped[int | None] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="CASCADE")
    )
    tipo: Mapped[TipoNotificacionEnum] = mapped_column(_tipo_notif_sa, nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    leida_at: Mapped[datetime | None] = mapped_column(DateTime)
