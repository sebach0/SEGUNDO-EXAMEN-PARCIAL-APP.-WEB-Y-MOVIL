# app/core/security.py
# =========================================================
# Utilidades de seguridad:
#   - Hashing de contraseñas (bcrypt via passlib)
#   - Creación y verificación de JWT (access + refresh tokens)
# =========================================================
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# ── Contexto de hashing (bcrypt) ────────────────────────────
# bcrypt es el estándar para contraseñas — computacionalmente costoso por diseño
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara contraseña en texto plano contra su hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ─────────────────────────────────────────────────────
def create_access_token(
    subject: Any,
    extra_claims: Optional[dict] = None
) -> str:
    """
    Crea un JWT de acceso (corta duración).
    
    Args:
        subject: Normalmente el ID del usuario (se convierte a str).
        extra_claims: Claims adicionales (ej: roles, jti, etc.)
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any, jti: str) -> str:
    """
    Crea un JWT de refresco (larga duración).
    El jti (JWT ID) permite revocar tokens individualmente.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "jti": jti,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si está expirado o es inválido.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
