# Seed idempotente: usuario ACTIVO con rol ADMIN (login panel web).
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.permisos.models import Permiso
from app.modules.acceso_y_administracion.roles.models import Rol, RolPermiso, UsuarioRol
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario

logger = logging.getLogger(__name__)


async def ensure_baseline_rol_permisos(db: AsyncSession) -> None:
    """
    Idempotente: asegura matriz rol↔permiso mínima en dev (BD creada antes del seed SQL).
    - ADMIN: todos los permisos del catálogo.
    - TALLER_RESPONSABLE: talleres crear/leer/actualizar.
    """
    now = utc_now_naive()
    r_admin = await db.execute(select(Rol).where(Rol.nombre == "ADMIN"))
    admin = r_admin.scalar_one_or_none()
    if admin is None:
        return

    res_all = await db.execute(select(Permiso.id))
    all_pids = [row[0] for row in res_all.fetchall()]
    res_have = await db.execute(
        select(RolPermiso.permiso_id).where(RolPermiso.rol_id == admin.id)
    )
    have_admin = {row[0] for row in res_have.fetchall()}
    for pid in all_pids:
        if pid not in have_admin:
            db.add(RolPermiso(rol_id=admin.id, permiso_id=pid, created_at=now))

    r_tr = await db.execute(select(Rol).where(Rol.nombre == "TALLER_RESPONSABLE"))
    tr = r_tr.scalar_one_or_none()
    if tr is None:
        return
    res_tp = await db.execute(
        select(Permiso.id).where(
            Permiso.codigo.in_(
                (
                    "talleres:crear",
                    "talleres:leer",
                    "talleres:actualizar",
                    "solicitudes_taller:leer",
                    "solicitudes_taller:aceptar",
                    "solicitudes_taller:rechazar",
                    "disponibilidad:gestionar",
                    "tecnicos:asignar",
                    "historial_atenciones:leer",
                    "comisiones:leer",
                )
            )
        )
    )
    taller_pids = [row[0] for row in res_tp.fetchall()]
    res_have_tr = await db.execute(
        select(RolPermiso.permiso_id).where(RolPermiso.rol_id == tr.id)
    )
    have_tr = {row[0] for row in res_have_tr.fetchall()}
    for pid in taller_pids:
        if pid not in have_tr:
            db.add(RolPermiso(rol_id=tr.id, permiso_id=pid, created_at=now))

    r_tc = await db.execute(select(Rol).where(Rol.nombre == "TECNICO"))
    tc = r_tc.scalar_one_or_none()
    if tc is not None:
        res_tc_perm = await db.execute(
            select(Permiso.id).where(
                Permiso.codigo.in_(
                    (
                        "servicios_tecnico:leer",
                        "cliente_ubicacion:leer",
                        "servicios_tecnico:actualizar_estado",
                        "mensajes_tecnico:crear",
                        "mensajes_tecnico:leer",
                        "mensajes:leer",
                        "mensajes:crear",
                        "notificaciones:leer",
                        "dispositivos:fcm",
                        "tecnico_ubicacion:compartir",
                    )
                )
            )
        )
        tc_pids = [row[0] for row in res_tc_perm.fetchall()]
        res_have_tc = await db.execute(
            select(RolPermiso.permiso_id).where(RolPermiso.rol_id == tc.id)
        )
        have_tc = {row[0] for row in res_have_tc.fetchall()}
        for pid in tc_pids:
            if pid not in have_tc:
                db.add(RolPermiso(rol_id=tc.id, permiso_id=pid, created_at=now))


async def ensure_dev_admin(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    """
    Crea o actualiza vínculo ADMIN para el email configurado.

    - Si ``require_enabled_flag`` es True, solo corre si ``SEED_ADMIN_ON_START``.
    - CLI: llamar con ``require_enabled_flag=False`` para forzar sin ese flag.
    """
    if require_enabled_flag and not settings.SEED_ADMIN_ON_START:
        return

    email = (settings.SEED_ADMIN_EMAIL or "").strip()
    password = settings.SEED_ADMIN_PASSWORD or ""
    telefono = (settings.SEED_ADMIN_TELEFONO or "").strip()
    if not email or not password or not telefono:
        logger.warning(
            "Seed admin omitido: definen SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD y SEED_ADMIN_TELEFONO."
        )
        return

    result = await db.execute(select(Rol).where(Rol.nombre == "ADMIN"))
    admin_rol = result.scalar_one_or_none()
    if admin_rol is None:
        logger.error("No existe rol ADMIN en BD. Aplica migrations/init.sql antes.")
        return

    await ensure_baseline_rol_permisos(db)

    now = utc_now_naive()
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    user = result.scalar_one_or_none()

    if user is not None:
        # Dev: misma cuenta en .env debe poder entrar tras cambiar SEED_ADMIN_PASSWORD
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            user.updated_at = now
            logger.info("Seed admin: contraseña alineada con env para %s", email)
        if user.estado != EstadoUsuarioEnum.ACTIVO:
            user.estado = EstadoUsuarioEnum.ACTIVO
            user.updated_at = now
            logger.info("Seed admin: estado ACTIVO para %s", email)

        link = await db.execute(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == user.id,
                UsuarioRol.rol_id == admin_rol.id,
            )
        )
        if link.scalar_one_or_none() is None:
            db.add(
                UsuarioRol(
                    usuario_id=user.id,
                    rol_id=admin_rol.id,
                    asignado_at=now,
                )
            )
            logger.info("Rol ADMIN asignado a usuario existente: %s", email)
        else:
            logger.info("Seed admin: usuario ya tenía ADMIN: %s", email)
        return

    u = Usuario(
        nombres=settings.SEED_ADMIN_NOMBRES,
        apellidos=settings.SEED_ADMIN_APELLIDOS,
        username=(settings.SEED_ADMIN_USERNAME or "").strip() or None,
        email=email,
        telefono=telefono,
        password_hash=hash_password(password),
        estado=EstadoUsuarioEnum.ACTIVO,
        created_at=now,
        updated_at=now,
    )
    db.add(u)
    await db.flush()
    db.add(
        UsuarioRol(
            usuario_id=u.id,
            rol_id=admin_rol.id,
            asignado_at=now,
        )
    )
    logger.info("Usuario administrador creado (seed): %s", email)
