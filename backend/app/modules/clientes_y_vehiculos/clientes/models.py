# Modelo ORM del perfil cliente (tabla clientes). La identidad de acceso vive en `usuarios.Usuario`.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cliente(Base):
    """
    Tabla: clientes
    Extensión de Usuario para clientes del sistema.
    Patrón: un Usuario tiene UN Cliente (relación 1:1).

    usuario_id: FK única — garantiza que un usuario solo sea cliente una vez.
    """

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    ciudad: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="cliente")
    vehiculos: Mapped[list["Vehiculo"]] = relationship("Vehiculo", back_populates="cliente")
