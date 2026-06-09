# app/modules/usuarios/service.py
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.core.timeutil import utc_now_naive
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.acceso_y_administracion.usuarios.models import Usuario, EstadoUsuarioEnum
from app.modules.acceso_y_administracion.usuarios.schemas import UsuarioListRead, UsuarioRead
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol


async def get_usuarios(db: AsyncSession) -> list[Usuario]:
    result = await db.execute(select(Usuario).order_by(Usuario.apellidos))
    return list(result.scalars().all())


async def get_usuarios_admin(db: AsyncSession) -> list[UsuarioListRead]:
    users = await get_usuarios(db)
    res = await db.execute(
        select(UsuarioRol.usuario_id, Rol.nombre).join(Rol, Rol.id == UsuarioRol.rol_id)
    )
    roles_by_user: defaultdict[int, list[str]] = defaultdict(list)
    for uid, nombre in res.fetchall():
        roles_by_user[uid].append(nombre)
    out: list[UsuarioListRead] = []
    for u in users:
        base = UsuarioRead.model_validate(u)
        out.append(UsuarioListRead(**base.model_dump(), roles=roles_by_user.get(u.id, [])))
    return out


async def get_usuario_by_id(usuario_id: int, db: AsyncSession) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def get_usuario_list_read(usuario_id: int, db: AsyncSession) -> UsuarioListRead:
    u = await get_usuario_by_id(usuario_id, db)
    res = await db.execute(
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    roles = [row[0] for row in res.fetchall()]
    base = UsuarioRead.model_validate(u)
    return UsuarioListRead(**base.model_dump(), roles=roles)


async def create_usuario(data: dict, db: AsyncSession, ejecutor_id: int | None = None) -> Usuario:
    # Verificar duplicados
    existing = await db.execute(select(Usuario).where(Usuario.email == data["email"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    existing_phone = await db.execute(select(Usuario).where(Usuario.telefono == data["telefono"]))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El teléfono ya está registrado")

    user = Usuario(
        nombres=data["nombres"],
        apellidos=data["apellidos"],
        email=data["email"],
        telefono=data["telefono"],
        username=data.get("username"),
        password_hash=hash_password(data["password"]),
        estado=data.get("estado", EstadoUsuarioEnum.ACTIVO),
        created_at=utc_now_naive(),
        updated_at=utc_now_naive(),
    )
    db.add(user)
    await db.flush()  # obtener ID sin commit

    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="usuarios",
        entidad="usuarios",
        entidad_id=user.id,
        accion=AccionBitacoraEnum.CREAR,
        descripcion=f"Creación del usuario {user.email}",
    )
    return user


async def update_usuario(
    usuario_id: int, data: dict, db: AsyncSession, ejecutor_id: int | None = None
) -> Usuario:
    user = await get_usuario_by_id(usuario_id, db)
    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)
    user.updated_at = utc_now_naive()

    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="usuarios",
        entidad="usuarios",
        entidad_id=usuario_id,
        accion=AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Actualización del usuario {usuario_id}",
    )
    return user


async def asignar_roles_usuario(
    usuario_id: int,
    rol_ids: list[int],
    db: AsyncSession,
    ejecutor_id: int,
) -> None:
    await get_usuario_by_id(usuario_id, db)
    from app.modules.acceso_y_administracion.roles import service as roles_service

    await roles_service.asignar_roles_usuario(usuario_id, rol_ids, db)
    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="roles",
        entidad="usuario_rol",
        entidad_id=usuario_id,
        accion=AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Asignación de roles al usuario {usuario_id}",
    )


async def reset_password_usuario(
    usuario_id: int, new_password: str, db: AsyncSession, ejecutor_id: int | None = None
) -> None:
    user = await get_usuario_by_id(usuario_id, db)
    user.password_hash = hash_password(new_password)
    user.estado = EstadoUsuarioEnum.ACTIVO
    user.updated_at = utc_now_naive()
    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="usuarios",
        entidad="usuarios",
        entidad_id=usuario_id,
        accion=AccionBitacoraEnum.RESTABLECER_CONTRASENA,
        descripcion=f"Reset de contraseña del usuario {usuario_id} por admin",
    )


async def delete_usuario(usuario_id: int, db: AsyncSession, ejecutor_id: int | None = None) -> None:
    """No elimina físicamente — cambia estado a INACTIVO (soft delete)."""
    user = await get_usuario_by_id(usuario_id, db)
    user.estado = EstadoUsuarioEnum.INACTIVO
    user.updated_at = utc_now_naive()
    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="usuarios",
        entidad="usuarios",
        entidad_id=usuario_id,
        accion=AccionBitacoraEnum.ELIMINAR,
        descripcion=f"Desactivación (soft delete) del usuario {usuario_id}",
    )


async def get_clientes(db: AsyncSession) -> list[Cliente]:
    result = await db.execute(select(Cliente))
    return list(result.scalars().all())


async def create_cliente(data: dict, db: AsyncSession) -> Cliente:
    cliente = Cliente(
        usuario_id=data["usuario_id"],
        ciudad=data.get("ciudad"),
        direccion=data.get("direccion"),
        created_at=utc_now_naive(),
        updated_at=utc_now_naive(),
    )
    db.add(cliente)
    await db.flush()
    return cliente
