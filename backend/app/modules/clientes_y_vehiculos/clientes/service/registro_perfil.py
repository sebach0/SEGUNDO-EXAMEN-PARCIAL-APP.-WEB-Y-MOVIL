from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.auth.email_tokens import crear_y_enviar_verificacion_email
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario

from ..models import Cliente
from ..schemas_movil import ClienteMiPerfilRead, ClienteMiPerfilUpdate, RegistroClienteMovilIn
from .acceso import get_cliente_row_for_usuario, require_cliente_rol
from .helpers import rol_id_por_nombre


async def registro_cliente_publico(body: RegistroClienteMovilIn, db: AsyncSession) -> ClienteMiPerfilRead:
    user = await usuarios_service.create_usuario(
        {
            "nombres": body.nombres.strip(),
            "apellidos": body.apellidos.strip(),
            "email": str(body.email).lower().strip(),
            "telefono": body.telefono.strip(),
            "password": body.password,
            "username": None,
            "estado": EstadoUsuarioEnum.PENDIENTE,
        },
        db,
        ejecutor_id=None,
    )
    cliente = await usuarios_service.create_cliente(
        {"usuario_id": user.id, "ciudad": None, "direccion": None},
        db,
    )
    rid = await rol_id_por_nombre(db, "CLIENTE")
    await asignar_roles_usuario(user.id, [rid], db)
    await registrar_accion(
        db,
        "clientes",
        "registro",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Registro público de cliente (app móvil): {user.email}",
        usuario_id=user.id,
        entidad_id=cliente.id,
    )
    await crear_y_enviar_verificacion_email(db, user)
    return await mi_perfil_read(user, cliente, db)


async def mi_perfil_read(user: Usuario, cliente: Cliente, db: AsyncSession) -> ClienteMiPerfilRead:
    _ = db
    return ClienteMiPerfilRead(
        usuario_id=user.id,
        cliente_id=cliente.id,
        nombres=user.nombres,
        apellidos=user.apellidos,
        email=user.email,
        telefono=user.telefono,
        ciudad=cliente.ciudad,
        direccion=cliente.direccion,
        pendiente_verificacion_email=(user.estado == EstadoUsuarioEnum.PENDIENTE),
    )


async def get_mi_perfil(user: Usuario, db: AsyncSession) -> ClienteMiPerfilRead:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)
    return await mi_perfil_read(user, cliente, db)


async def update_mi_perfil(user: Usuario, body: ClienteMiPerfilUpdate, db: AsyncSession) -> ClienteMiPerfilRead:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)

    udata = {
        "nombres": body.nombres,
        "apellidos": body.apellidos,
        "telefono": body.telefono,
        "username": None,
        "estado": None,
    }
    udata = {k: v for k, v in udata.items() if v is not None}
    if udata:
        user = await usuarios_service.update_usuario(user.id, udata, db, ejecutor_id=user.id)
        await db.refresh(user)

    if body.ciudad is not None:
        cliente.ciudad = body.ciudad
    if body.direccion is not None:
        cliente.direccion = body.direccion
    cliente.updated_at = utc_now_naive()

    await registrar_accion(
        db,
        "clientes",
        "clientes",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion="Actualización de perfil cliente (app móvil)",
        usuario_id=user.id,
        entidad_id=cliente.id,
    )
    return await mi_perfil_read(user, cliente, db)
