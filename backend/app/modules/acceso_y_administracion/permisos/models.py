# app/modules/permisos/models.py
# Permisos atómicos (tabla permisos). Relación M:N con roles vía roles.models.RolPermiso.
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.acceso_y_administracion.roles.models import RolPermiso


class Permiso(Base):
    """
    Tabla: permisos
    Permiso atómico identificado por un código único.
    Ejemplos: usuarios:crear, vehiculos:leer, talleres:actualizar
    """

    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    rol_permisos: Mapped[list["RolPermiso"]] = relationship(
        "RolPermiso", back_populates="permiso"
    )
