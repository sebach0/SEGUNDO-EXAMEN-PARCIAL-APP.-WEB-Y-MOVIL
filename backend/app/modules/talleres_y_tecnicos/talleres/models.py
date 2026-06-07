# app/modules/talleres/models.py
# =========================================================
# Modelos SQLAlchemy para el módulo de Talleres:
#   Taller, EspecialidadTecnico, Tecnico, ServicioCatalogo, TallerServicio
# =========================================================
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, DateTime, Enum as SAEnum, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.acceso_y_administracion.usuarios.models import Usuario


# ── ENUMs ───────────────────────────────────────────────────
class EstadoTallerEnum(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    PENDIENTE = "PENDIENTE"


class EstadoTecnicoEnum(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


# ── Modelo: Taller ──────────────────────────────────────────
class Taller(Base):
    """
    Tabla: talleres
    Taller mecánico con un usuario responsable (FK a usuarios).
    usuario_responsable_id UNIQUE garantiza que un usuario solo
    puede ser responsable de un taller.
    """
    __tablename__ = "talleres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_responsable_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    nombre_comercial: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono_contacto: Mapped[str] = mapped_column(String(30), nullable=False)
    email_contacto: Mapped[str] = mapped_column(String(120), nullable=False)
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[EstadoTallerEnum] = mapped_column(
        SAEnum(EstadoTallerEnum, name="estado_taller"), nullable=False
    )
    tiene_grua: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relaciones
    tecnicos: Mapped[list["Tecnico"]] = relationship(back_populates="taller")
    taller_servicios: Mapped[list["TallerServicio"]] = relationship(
        back_populates="taller", cascade="all, delete-orphan"
    )


# ── Modelo: EspecialidadTecnico ─────────────────────────────
class EspecialidadTecnico(Base):
    """
    Tabla: especialidades_tecnico
    Catálogo de especialidades: Motor, Electricidad, Carrocería, etc.
    """
    __tablename__ = "especialidades_tecnico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))


# ── Modelo: Tecnico ─────────────────────────────────────────
class Tecnico(Base):
    """
    Tabla: tecnicos
    Técnico asociado a un Taller. Extensión de Usuario (patrón 1:1).
    especialidad_id es nullable — ON DELETE SET NULL.
    """
    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False
    )
    especialidad_id: Mapped[int | None] = mapped_column(
        ForeignKey("especialidades_tecnico.id", ondelete="SET NULL")
    )
    documento_identidad: Mapped[str | None] = mapped_column(String(50), nullable=True)
    disponibilidad: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estado: Mapped[EstadoTecnicoEnum] = mapped_column(
        SAEnum(EstadoTecnicoEnum, name="estado_tecnico"), nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relaciones
    taller: Mapped["Taller"] = relationship(back_populates="tecnicos")
    especialidad: Mapped["EspecialidadTecnico | None"] = relationship()
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])


# ── Modelo: ServicioCatalogo ────────────────────────────────
class ServicioCatalogo(Base):
    """
    Tabla: servicios_catalogo
    Catálogo de tipos de servicio: Chaperío, Llantería, Grúa, etc.
    """
    __tablename__ = "servicios_catalogo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    taller_servicios: Mapped[list["TallerServicio"]] = relationship(back_populates="servicio")


# ── Modelo: TallerServicio ──────────────────────────────────
class TallerServicio(Base):
    """
    Tabla: taller_servicios
    Relación N:M entre Taller y ServicioCatalogo.
    Un taller puede ofrecer múltiples servicios.
    """
    __tablename__ = "taller_servicios"
    __table_args__ = (UniqueConstraint("taller_id", "servicio_id", name="uq_taller_servicio"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    taller_id: Mapped[int] = mapped_column(
        ForeignKey("talleres.id", ondelete="CASCADE"), nullable=False
    )
    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios_catalogo.id", ondelete="CASCADE"), nullable=False
    )

    taller: Mapped["Taller"] = relationship(back_populates="taller_servicios")
    servicio: Mapped["ServicioCatalogo"] = relationship(back_populates="taller_servicios")
