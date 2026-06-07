# ORM — tabla tenants (raíz multi-tenant SaaS)
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EstadoTenantEnum(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class Tenant(Base):
    """
    Tabla: tenants
    Unidad de aislamiento SaaS. Cada red de talleres u organización tiene su propio tenant.
    Todos los datos operativos (usuarios, incidentes, talleres, KPIs) quedan filtrados por tenant_id.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
