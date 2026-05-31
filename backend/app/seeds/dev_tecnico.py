# Usuario rol TECNICO + fila tecnicos (usa el primer taller; ejecutar después del seed taller).
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.talleres_y_tecnicos.talleres import service as talleres_service
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTecnicoEnum, Taller, Tecnico
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario

logger = logging.getLogger(__name__)


async def _rol_tecnico_id(db: AsyncSession) -> int | None:
    r = await db.execute(select(Rol.id).where(Rol.nombre == "TECNICO"))
    x = r.scalar_one_or_none()
    return int(x) if x is not None else None


async def ensure_dev_tecnico(db: AsyncSession, *, require_enabled_flag: bool = True) -> None:
    if require_enabled_flag and not settings.SEED_TECNICO_ON_START:
        return
    email = (settings.SEED_TECNICO_EMAIL or "").strip()
    pwd = settings.SEED_TECNICO_PASSWORD or ""
    tel = (settings.SEED_TECNICO_TELEFONO or "").strip()
    if not email or not pwd or not tel:
        logger.warning("Seed técnico omitido (faltan email/password/tel).")
        return
    tr = await db.execute(select(Taller).order_by(Taller.id).limit(1))
    taller = tr.scalar_one_or_none()
    if taller is None:
        logger.warning("Seed técnico omitido: no hay taller (corré seed taller antes).")
        return
    rid = await _rol_tecnico_id(db)
    if rid is None:
        return
    now = utc_now_naive()
    res = await db.execute(select(Usuario).where(Usuario.email == email))
    user = res.scalar_one_or_none()
    if user is not None:
        if not verify_password(pwd, user.password_hash):
            user.password_hash = hash_password(pwd)
            user.updated_at = now
        user.estado = EstadoUsuarioEnum.ACTIVO
        user.updated_at = now
    else:
        user = await usuarios_service.create_usuario(
            {
                "nombres": settings.SEED_TECNICO_NOMBRES,
                "apellidos": settings.SEED_TECNICO_APELLIDOS,
                "email": email,
                "telefono": tel,
                "password": pwd,
                "username": None,
                "estado": EstadoUsuarioEnum.ACTIVO,
            },
            db,
            ejecutor_id=None,
        )
    await asignar_roles_usuario(user.id, [rid], db)
    ex = (await db.execute(select(Tecnico).where(Tecnico.usuario_id == user.id))).scalar_one_or_none()
    if ex is not None:
        if ex.taller_id != taller.id:
            ex.taller_id = taller.id
            ex.updated_at = now
        return
    await talleres_service.create_tecnico(
        {
            "usuario_id": user.id,
            "taller_id": taller.id,
            "especialidad_id": None,
            "estado": EstadoTecnicoEnum.ACTIVO,
        },
        db,
        ejecutor_id=user.id,
    )
    logger.info("Seed técnico ok: %s", email)
