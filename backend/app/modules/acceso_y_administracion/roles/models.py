# app/modules/roles/models.py
# Roles, pivots usuario↔rol y rol↔permiso.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.acceso_y_administracion.permisos.models import Permiso


class Rol(Base):
    """Tabla: roles — grupos de permisos asignables a usuarios."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    rol_permisos: Mapped[list["RolPermiso"]] = relationship(back_populates="rol")
    usuario_roles: Mapped[list["UsuarioRol"]] = relationship(back_populates="rol")


class RolPermiso(Base):
    """Tabla: rol_permiso — asociación muchos-a-muchos entre Rol y Permiso."""

    __tablename__ = "rol_permiso"
    __table_args__ = (UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    permiso_id: Mapped[int] = mapped_column(
        ForeignKey("permisos.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime)

    rol: Mapped["Rol"] = relationship(back_populates="rol_permisos")
    permiso: Mapped["Permiso"] = relationship(back_populates="rol_permisos")


class UsuarioRol(Base):
    """Tabla: usuario_rol — asociación muchos-a-muchos entre Usuario y Rol."""

    __tablename__ = "usuario_rol"
    __table_args__ = (UniqueConstraint("usuario_id", "rol_id", name="uq_usuario_rol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    asignado_at: Mapped[datetime | None] = mapped_column(DateTime)

    rol: Mapped["Rol"] = relationship(back_populates="usuario_roles")
