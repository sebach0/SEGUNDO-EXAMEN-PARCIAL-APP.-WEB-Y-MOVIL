# app/modules/vehiculos/models.py
from __future__ import annotations

# =========================================================
# Modelos SQLAlchemy para el módulo de Vehículos:
#   MarcaVehiculo, ModeloVehiculo, TipoVehiculo, Vehiculo
# =========================================================
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.clientes_y_vehiculos.clientes.models import Cliente


# ── Modelo: MarcaVehiculo ───────────────────────────────────
class MarcaVehiculo(Base):
    """
    Tabla: marcas_vehiculo
    Catálogo de marcas (Toyota, Ford, Chevrolet...).
    Separar en tabla propia permite agregar nuevas marcas sin modificar vehículos.
    """
    __tablename__ = "marcas_vehiculo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)

    # Relaciones
    modelos: Mapped[list["ModeloVehiculo"]] = relationship(back_populates="marca")


# ── Modelo: ModeloVehiculo ──────────────────────────────────
class ModeloVehiculo(Base):
    """
    Tabla: modelos_vehiculo
    Modelos pertenecen a una marca. Constraint UNIQUE(marca_id, nombre)
    evita duplicar "Corolla" bajo Toyota, pero permite otro "Corolla" simulado.
    """
    __tablename__ = "modelos_vehiculo"
    __table_args__ = (
        UniqueConstraint("marca_id", "nombre", name="uq_modelos_vehiculo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca_id: Mapped[int] = mapped_column(
        ForeignKey("marcas_vehiculo.id", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)

    # Relaciones
    marca: Mapped["MarcaVehiculo"] = relationship(back_populates="modelos")


# ── Modelo: TipoVehiculo ────────────────────────────────────
class TipoVehiculo(Base):
    """
    Tabla: tipos_vehiculo
    Catálogo de tipos: Sedán, SUV, Pickup, Moto, etc.
    """
    __tablename__ = "tipos_vehiculo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


# ── Modelo: Vehiculo ────────────────────────────────────────
class Vehiculo(Base):
    """
    Tabla: vehiculos
    Vehículo propiedad de un Cliente. Referencia marca, modelo y tipo
    mediante FKs a los catálogos. La placa es única a nivel nacional.
    """
    __tablename__ = "vehiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    placa: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    marca_id: Mapped[int] = mapped_column(
        ForeignKey("marcas_vehiculo.id", ondelete="RESTRICT"), nullable=False
    )
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("modelos_vehiculo.id", ondelete="RESTRICT"), nullable=False
    )
    tipo_vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"), nullable=False
    )
    anio: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relaciones
    cliente: Mapped[Cliente] = relationship(back_populates="vehiculos")
    marca: Mapped["MarcaVehiculo"] = relationship()
    modelo: Mapped["ModeloVehiculo"] = relationship()
    tipo_vehiculo: Mapped["TipoVehiculo"] = relationship()
