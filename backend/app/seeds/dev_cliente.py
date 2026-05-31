# Seed idempotente: usuario + fila cliente + rol CLIENTE (login app móvil / pruebas).
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario

logger = logging.getLogger(__name__)


async def _rol_cliente_id(db: AsyncSession) -> int | None:
    r = await db.execute(select(Rol.id).where(Rol.nombre == "CLIENTE"))
    row = r.scalar_one_or_none()
    if row is None:
        logger.error("Seed cliente: no existe rol CLIENTE. Aplica migrations/init.sql.")
        return None
    return int(row)


async def ensure_dev_cliente(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    """Usuario CLIENTE + fila clientes. CLI: require_enabled_flag=False."""
    if require_enabled_flag and not settings.SEED_CLIENTE_ON_START:
        return

    email = (settings.SEED_CLIENTE_EMAIL or "").strip()
    password = settings.SEED_CLIENTE_PASSWORD or ""
    telefono = (settings.SEED_CLIENTE_TELEFONO or "").strip()
    if not email or not password or not telefono:
        logger.warning(
            "Seed cliente omitido: definen SEED_CLIENTE_EMAIL, SEED_CLIENTE_PASSWORD y SEED_CLIENTE_TELEFONO."
        )
        return

    rol_id = await _rol_cliente_id(db)
    if rol_id is None:
        return

    now = utc_now_naive()
    res = await db.execute(select(Usuario).where(Usuario.email == email))
    user = res.scalar_one_or_none()

    if user is not None:
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            user.updated_at = now
            logger.info("Seed cliente: contraseña alineada con env para %s", email)
        if user.estado != EstadoUsuarioEnum.ACTIVO:
            user.estado = EstadoUsuarioEnum.ACTIVO
            user.updated_at = now

        c_res = await db.execute(select(Cliente).where(Cliente.usuario_id == user.id))
        cliente = c_res.scalar_one_or_none()
        if cliente is None:
            await usuarios_service.create_cliente(
                {
                    "usuario_id": user.id,
                    "ciudad": (settings.SEED_CLIENTE_CIUDAD or "").strip() or None,
                    "direccion": (settings.SEED_CLIENTE_DIRECCION or "").strip() or None,
                },
                db,
            )
            logger.info("Seed cliente: fila clientes creada para usuario existente %s", email)
        else:
            if settings.SEED_CLIENTE_CIUDAD is not None:
                cliente.ciudad = settings.SEED_CLIENTE_CIUDAD.strip() or None
            if settings.SEED_CLIENTE_DIRECCION is not None:
                cliente.direccion = (settings.SEED_CLIENTE_DIRECCION or "").strip() or None
            cliente.updated_at = now

        await asignar_roles_usuario(user.id, [rol_id], db)
        logger.info("Seed cliente: rol CLIENTE asegurado para %s", email)
        return

    u = await usuarios_service.create_usuario(
        {
            "nombres": settings.SEED_CLIENTE_NOMBRES,
            "apellidos": settings.SEED_CLIENTE_APELLIDOS,
            "email": email,
            "telefono": telefono,
            "password": password,
            "username": None,
            "estado": EstadoUsuarioEnum.ACTIVO,
        },
        db,
        ejecutor_id=None,
    )
    await usuarios_service.create_cliente(
        {
            "usuario_id": u.id,
            "ciudad": (settings.SEED_CLIENTE_CIUDAD or "").strip() or None,
            "direccion": (settings.SEED_CLIENTE_DIRECCION or "").strip() or None,
        },
        db,
    )
    await asignar_roles_usuario(u.id, [rol_id], db)
    logger.info("Usuario cliente demo creado (seed): %s", email)
