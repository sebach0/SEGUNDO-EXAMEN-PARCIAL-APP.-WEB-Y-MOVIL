# Seed idempotente: usuario responsable + rol TALLER_RESPONSABLE + taller (pruebas portal / web).
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.talleres_y_tecnicos.talleres import service as talleres_service
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTallerEnum, Taller
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario
from app.seeds.identidades_demo_sc import TALLER_PRINCIPAL_LAT, TALLER_PRINCIPAL_LNG

logger = logging.getLogger(__name__)


async def _rol_taller_responsable_id(db: AsyncSession) -> int | None:
    r = await db.execute(select(Rol.id).where(Rol.nombre == "TALLER_RESPONSABLE"))
    row = r.scalar_one_or_none()
    if row is None:
        logger.error("Seed taller: no existe rol TALLER_RESPONSABLE. Aplica migrations/init.sql.")
        return None
    return int(row)


def _taller_payload(user_id: int, email: str, telefono: str) -> dict:
    return {
        "usuario_responsable_id": user_id,
        "nombre_comercial": settings.SEED_TALLER_NOMBRE_COMERCIAL,
        "telefono_contacto": telefono,
        "email_contacto": email,
        "direccion": settings.SEED_TALLER_DIRECCION,
        "ciudad": settings.SEED_TALLER_CIUDAD,
        "latitud": TALLER_PRINCIPAL_LAT,
        "longitud": TALLER_PRINCIPAL_LNG,
        "descripcion": settings.SEED_TALLER_DESCRIPCION,
        "estado": EstadoTallerEnum.ACTIVO,
    }


async def _apply_taller_demo_fields(taller: Taller, email: str, telefono: str) -> None:
    taller.nombre_comercial = settings.SEED_TALLER_NOMBRE_COMERCIAL
    taller.telefono_contacto = telefono
    taller.email_contacto = email
    taller.direccion = settings.SEED_TALLER_DIRECCION
    taller.ciudad = settings.SEED_TALLER_CIUDAD
    taller.latitud = TALLER_PRINCIPAL_LAT
    taller.longitud = TALLER_PRINCIPAL_LNG
    taller.descripcion = settings.SEED_TALLER_DESCRIPCION
    taller.estado = EstadoTallerEnum.ACTIVO
    taller.updated_at = utc_now_naive()


async def _ensure_taller_row(
    db: AsyncSession,
    user: Usuario,
    email: str,
    telefono: str,
) -> None:
    """Un taller por responsable; savepoint ante carreras."""
    await db.flush()
    t_res = await db.execute(select(Taller).where(Taller.usuario_responsable_id == user.id))
    taller = t_res.scalar_one_or_none()
    if taller is not None:
        await _apply_taller_demo_fields(taller, email, telefono)
        logger.info("Seed taller: taller ya existía, datos actualizados (usuario_id=%s)", user.id)
        return

    async with db.begin_nested():
        try:
            await talleres_service.create_taller(
                _taller_payload(user.id, email, telefono),
                db,
                ejecutor_id=user.id,
            )
        except IntegrityError:
            logger.warning(
                "Seed taller: inserción duplicada ignorada (carrera o reintento; usuario_id=%s)",
                user.id,
            )

    t_res2 = await db.execute(select(Taller).where(Taller.usuario_responsable_id == user.id))
    taller = t_res2.scalar_one_or_none()
    if taller is None:
        logger.error(
            "Seed taller: no hay fila taller tras upsert para usuario_id=%s. Revisa constraints.",
            user.id,
        )
        return
    await _apply_taller_demo_fields(taller, email, telefono)
    logger.info("Seed taller: taller asegurado para usuario_id=%s", user.id)


async def ensure_dev_taller(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    """Usuario TALLER_RESPONSABLE + taller ACTIVO. CLI usa require_enabled_flag=False."""
    if require_enabled_flag and not settings.SEED_TALLER_ON_START:
        return

    email = (settings.SEED_TALLER_EMAIL or "").strip()
    password = settings.SEED_TALLER_PASSWORD or ""
    telefono = (settings.SEED_TALLER_TELEFONO or "").strip()
    if not email or not password or not telefono:
        logger.warning(
            "Seed taller omitido: definen SEED_TALLER_EMAIL, SEED_TALLER_PASSWORD y SEED_TALLER_TELEFONO."
        )
        return

    rol_id = await _rol_taller_responsable_id(db)
    if rol_id is None:
        return

    now = utc_now_naive()
    res = await db.execute(select(Usuario).where(Usuario.email == email))
    user = res.scalar_one_or_none()

    if user is not None:
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            user.updated_at = now
            logger.info("Seed taller: contraseña alineada con env para %s", email)
        if user.estado != EstadoUsuarioEnum.ACTIVO:
            user.estado = EstadoUsuarioEnum.ACTIVO
            user.updated_at = now

        await asignar_roles_usuario(user.id, [rol_id], db)
        await _ensure_taller_row(db, user, email, telefono)
        return

    u = await usuarios_service.create_usuario(
        {
            "nombres": settings.SEED_TALLER_RESPONSABLE_NOMBRES,
            "apellidos": settings.SEED_TALLER_RESPONSABLE_APELLIDOS,
            "email": email,
            "telefono": telefono,
            "password": password,
            "username": None,
            "estado": EstadoUsuarioEnum.ACTIVO,
        },
        db,
        ejecutor_id=None,
    )
    await asignar_roles_usuario(u.id, [rol_id], db)
    await _ensure_taller_row(db, u, email, telefono)
    logger.info("Usuario responsable de taller demo creado (seed): %s", email)
