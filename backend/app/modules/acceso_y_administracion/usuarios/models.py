# app/modules/usuarios/models.py
from __future__ import annotations

# =========================================================
# Modelos SQLAlchemy para el módulo de Usuarios: Usuario.
# El perfil de negocio `Cliente` vive en `app.modules.clientes_y_vehiculos.clientes.models`.
# =========================================================
import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# ── ENUMs ───────────────────────────────────────────────────
class EstadoUsuarioEnum(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    BLOQUEADO = "BLOQUEADO"
    PENDIENTE = "PENDIENTE"


# ── Modelo: Usuario ─────────────────────────────────────────
class Usuario(Base):
    """
    Tabla: usuarios
    Entidad central del sistema — toda persona con acceso hereda de aquí.
    Clientes, técnicos y responsables de talleres son extensiones de Usuario.
    
    password_hash: NUNCA se almacena el password en texto plano.
    estado: controla si puede iniciar sesión.
    """
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # tenant_id: NULL para usuarios Ciclo 1-3; la migración 0015 lo rellena con el tenant principal.
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoUsuarioEnum] = mapped_column(
        SAEnum(EstadoUsuarioEnum, name="estado_usuario"), nullable=False
    )
    ultimo_acceso_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relaciones (Cliente en módulo `clientes`)
    cliente: Mapped["Cliente | None"] = relationship(
        "Cliente",
        back_populates="usuario",
        uselist=False,
    )
