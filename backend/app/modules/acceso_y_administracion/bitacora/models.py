# app/modules/bitacora/models.py
# =========================================================
# Modelo SQLAlchemy para la Bitácora de auditoría
# =========================================================
import enum
from datetime import datetime
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AccionBitacoraEnum(str, enum.Enum):
    CREAR = "CREAR"
    ACTUALIZAR = "ACTUALIZAR"
    ELIMINAR = "ELIMINAR"
    INICIAR_SESION = "INICIAR_SESION"
    CERRAR_SESION = "CERRAR_SESION"
    RESTABLECER_CONTRASENA = "RESTABLECER_CONTRASENA"
    ASIGNAR_ROL = "ASIGNAR_ROL"
    ASIGNAR_PERMISO = "ASIGNAR_PERMISO"
    CONSULTAR = "CONSULTAR"


class Bitacora(Base):
    """
    Tabla: bitacora
    Registro inmutable de acciones del sistema.
    
    - usuario_id puede ser NULL (FK ON DELETE SET NULL) porque si
      un usuario es eliminado, el log histórico debe mantenerse.
    - modulo + entidad + entidad_id: identifican exactamente QUÉ fue afectado.
    - ip_address: trazabilidad de origen de la acción.
    
    IMPORTANTE: Esta tabla solo se escribe, nunca se modifica ni elimina.
    """
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    modulo: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    accion: Mapped[AccionBitacoraEnum] = mapped_column(
        SAEnum(AccionBitacoraEnum, name="accion_bitacora"), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
