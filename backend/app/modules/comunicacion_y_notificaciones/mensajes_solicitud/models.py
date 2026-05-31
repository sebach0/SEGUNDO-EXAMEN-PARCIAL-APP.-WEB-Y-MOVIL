from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SolicitudMensaje(Base):
    __tablename__ = "solicitud_mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_emergencia.id", ondelete="CASCADE"), nullable=False
    )
    emisor_usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    receptor_usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    leido_at: Mapped[datetime | None] = mapped_column(DateTime)
