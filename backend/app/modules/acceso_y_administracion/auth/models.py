# app/modules/auth/models.py
# Sesiones JWT y tokens opacos de email (verificación / reset).
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EstadoSesionEnum(str, enum.Enum):
    ACTIVA = "ACTIVA"
    CERRADA = "CERRADA"
    EXPIRADA = "EXPIRADA"
    REVOCADA = "REVOCADA"


class Sesion(Base):
    """
    Tabla: sesiones — registro de sesión; token_jti es el JWT ID para revocación.
    """

    __tablename__ = "sesiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    dispositivo: Mapped[str | None] = mapped_column(String(100))
    plataforma: Mapped[str | None] = mapped_column(String(50))
    iniciado_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cerrado_at: Mapped[datetime | None] = mapped_column(DateTime)
    expira_at: Mapped[datetime | None] = mapped_column(DateTime)
    estado: Mapped[EstadoSesionEnum] = mapped_column(
        SAEnum(EstadoSesionEnum, name="estado_sesion"), nullable=False
    )


class UsuarioTokenSeguridad(Base):
    """Tabla usuario_tokens_seguridad — token opaco guardado como SHA-256 hex."""

    __tablename__ = "usuario_tokens_seguridad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    usado_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
