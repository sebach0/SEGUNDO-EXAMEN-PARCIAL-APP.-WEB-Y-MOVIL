# app/modules/roles/service.py
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.permisos.models import Permiso
from app.modules.acceso_y_administracion.roles.models import Rol, RolPermiso, UsuarioRol


async def get_roles(db: AsyncSession) -> list[Rol]:
    result = await db.execute(select(Rol).order_by(Rol.nombre))
    return list(result.scalars().all())


async def get_permiso_ids_for_rol(rol_id: int, db: AsyncSession) -> list[int]:
    res = await db.execute(
        select(RolPermiso.permiso_id).where(RolPermiso.rol_id == rol_id)
    )
    return [row[0] for row in res.fetchall()]


async def create_rol(nombre: str, descripcion: str | None, db: AsyncSession) -> Rol:
    rol = Rol(
        nombre=nombre,
        descripcion=descripcion,
        created_at=utc_now_naive(),
        updated_at=utc_now_naive(),
    )
    db.add(rol)
    await db.flush()
    return rol


async def asignar_permisos_rol(rol_id: int, permiso_ids: list[int], db: AsyncSession) -> None:
    """Reemplaza todos los permisos del rol por los nuevos."""
    await db.execute(delete(RolPermiso).where(RolPermiso.rol_id == rol_id))
    for pid in permiso_ids:
        db.add(
            RolPermiso(
                rol_id=rol_id,
                permiso_id=pid,
                created_at=utc_now_naive(),
            )
        )


async def asignar_roles_usuario(usuario_id: int, rol_ids: list[int], db: AsyncSession) -> None:
    """Reemplaza todos los roles del usuario por los nuevos."""
    await db.execute(delete(UsuarioRol).where(UsuarioRol.usuario_id == usuario_id))
    for rid in rol_ids:
        db.add(
            UsuarioRol(
                usuario_id=usuario_id,
                rol_id=rid,
                asignado_at=utc_now_naive(),
            )
        )
