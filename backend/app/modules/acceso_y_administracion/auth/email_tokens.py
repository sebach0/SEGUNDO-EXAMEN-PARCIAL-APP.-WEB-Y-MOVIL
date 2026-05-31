# Tokens por correo: verificación de cuenta y restablecimiento de contraseña.
from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.mail import send_plain_email
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.auth.models import UsuarioTokenSeguridad
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario

TIPO_VERIFICAR_EMAIL = "VERIFICAR_EMAIL"
TIPO_RESTABLECER_PASSWORD = "RESTABLECER_PASSWORD"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _nuevo_token_raw() -> str:
    return secrets.token_urlsafe(32)


async def _invalidar_pendientes(
    db: AsyncSession, *, usuario_id: int, tipo: str
) -> None:
    await db.execute(
        delete(UsuarioTokenSeguridad).where(
            UsuarioTokenSeguridad.usuario_id == usuario_id,
            UsuarioTokenSeguridad.tipo == tipo,
            UsuarioTokenSeguridad.usado_at.is_(None),
        )
    )


async def crear_y_enviar_verificacion_email(db: AsyncSession, user: Usuario) -> None:
    raw = _nuevo_token_raw()
    th = _hash_token(raw)
    now = utc_now_naive()
    exp = now + timedelta(hours=72)
    await _invalidar_pendientes(db, usuario_id=user.id, tipo=TIPO_VERIFICAR_EMAIL)
    db.add(
        UsuarioTokenSeguridad(
            usuario_id=user.id,
            tipo=TIPO_VERIFICAR_EMAIL,
            token_hash=th,
            expires_at=exp,
            usado_at=None,
            created_at=now,
        )
    )
    await db.flush()
    base = settings.api_public_base_url
    prefix = settings.API_PREFIX.rstrip("/")
    url = f"{base}{prefix}/auth/verificar-email?token={raw}"
    body = (
        f"Hola {user.nombres},\n\n"
        f"Gracias por registrarte en {settings.PROJECT_NAME}.\n"
        f"Para activar tu cuenta abre este enlace (válido 72 h):\n\n{url}\n\n"
        f"Si no creaste esta cuenta, ignora este mensaje.\n"
    )
    await send_plain_email(user.email, "Verifica tu correo — Emergencias Viales", body)


async def crear_y_enviar_reset_password(db: AsyncSession, user: Usuario) -> None:
    raw = _nuevo_token_raw()
    th = _hash_token(raw)
    now = utc_now_naive()
    exp = now + timedelta(hours=2)
    await _invalidar_pendientes(db, usuario_id=user.id, tipo=TIPO_RESTABLECER_PASSWORD)
    db.add(
        UsuarioTokenSeguridad(
            usuario_id=user.id,
            tipo=TIPO_RESTABLECER_PASSWORD,
            token_hash=th,
            expires_at=exp,
            usado_at=None,
            created_at=now,
        )
    )
    await db.flush()
    fe = settings.app_public_base_url
    url = f"{fe}/taller/restablecer-contrasena?token={raw}"
    body = (
        f"Hola {user.nombres},\n\n"
        f"Recibimos una solicitud para restablecer la contraseña de tu cuenta.\n"
        f"Abre este enlace (válido 2 h):\n\n{url}\n\n"
        f"Si no fuiste tú, ignora este mensaje.\n"
    )
    await send_plain_email(user.email, "Restablecer contraseña — Emergencias Viales", body)


async def consumir_token_verificar_email(db: AsyncSession, raw_token: str) -> Usuario | None:
    th = _hash_token(raw_token)
    now = utc_now_naive()
    res = await db.execute(
        select(UsuarioTokenSeguridad).where(
            UsuarioTokenSeguridad.tipo == TIPO_VERIFICAR_EMAIL,
            UsuarioTokenSeguridad.token_hash == th,
            UsuarioTokenSeguridad.usado_at.is_(None),
            UsuarioTokenSeguridad.expires_at > now,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        return None
    ures = await db.execute(select(Usuario).where(Usuario.id == row.usuario_id))
    user = ures.scalar_one_or_none()
    if user is None:
        return None
    user.estado = EstadoUsuarioEnum.ACTIVO
    user.updated_at = now
    await db.execute(
        update(UsuarioTokenSeguridad)
        .where(UsuarioTokenSeguridad.id == row.id)
        .values(usado_at=now)
    )
    return user


async def consumir_token_reset_password(
    db: AsyncSession, raw_token: str, new_password_plain: str
) -> Usuario | None:
    from app.core.security import hash_password

    th = _hash_token(raw_token)
    now = utc_now_naive()
    res = await db.execute(
        select(UsuarioTokenSeguridad).where(
            UsuarioTokenSeguridad.tipo == TIPO_RESTABLECER_PASSWORD,
            UsuarioTokenSeguridad.token_hash == th,
            UsuarioTokenSeguridad.usado_at.is_(None),
            UsuarioTokenSeguridad.expires_at > now,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        return None
    ures = await db.execute(select(Usuario).where(Usuario.id == row.usuario_id))
    user = ures.scalar_one_or_none()
    if user is None:
        return None
    user.password_hash = hash_password(new_password_plain)
    user.estado = EstadoUsuarioEnum.ACTIVO
    user.updated_at = now
    await db.execute(
        update(UsuarioTokenSeguridad)
        .where(UsuarioTokenSeguridad.id == row.id)
        .values(usado_at=now)
    )
    return user
