# Lógica del portal taller (ciclo 1).
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.auth.email_tokens import crear_y_enviar_verificacion_email
from app.modules.acceso_y_administracion.usuarios.models import Usuario, EstadoUsuarioEnum
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.talleres_y_tecnicos.talleres.models import (
    Taller,
    Tecnico,
    EspecialidadTecnico,
    EstadoTecnicoEnum,
    EstadoTallerEnum,
)
from app.modules.talleres_y_tecnicos.talleres import service as talleres_service
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum

from .schemas import (
    RegistroTallerIn,
    MiTallerRead,
    MiTallerUpdate,
    TecnicoPortalCreate,
    TecnicoPortalUpdate,
    TecnicoPortalRead,
    TallerDashboardRead,
)


def _split_nombre_completo(full: str) -> tuple[str, str]:
    parts = full.strip().split()
    if not parts:
        return "Sin", "Nombre"
    if len(parts) == 1:
        return parts[0], "."
    return " ".join(parts[:-1]), parts[-1]


async def _rol_id_by_nombre(db: AsyncSession, nombre: str) -> int:
    r = await db.execute(select(Rol.id).where(Rol.nombre == nombre))
    row = r.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rol '{nombre}' no configurado en el sistema.",
        )
    return int(row)


async def registro_taller_publico(body: RegistroTallerIn, db: AsyncSession) -> MiTallerRead:
    """Crea usuario responsable, rol TALLER_RESPONSABLE y taller en estado PENDIENTE."""
    nombres, apellidos = _split_nombre_completo(body.responsable_nombre_completo)
    dup_tel = await db.execute(select(Usuario).where(Usuario.telefono == body.telefono))
    if dup_tel.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El teléfono ya está registrado.")

    user = await usuarios_service.create_usuario(
        {
            "nombres": nombres,
            "apellidos": apellidos,
            "email": str(body.email),
            "telefono": body.telefono,
            "password": body.password,
            "username": None,
            "estado": EstadoUsuarioEnum.PENDIENTE,
        },
        db,
        ejecutor_id=None,
    )
    rid = await _rol_id_by_nombre(db, "TALLER_RESPONSABLE")
    await asignar_roles_usuario(user.id, [rid], db)
    await registrar_accion(
        db=db,
        usuario_id=user.id,
        modulo="taller_responsable",
        entidad="registro",
        entidad_id=user.id,
        accion=AccionBitacoraEnum.CREAR,
        descripcion=f"Registro público de taller para {user.email}",
    )

    taller = await talleres_service.create_taller(
        {
            "usuario_responsable_id": user.id,
            "nombre_comercial": body.nombre_comercial,
            "telefono_contacto": body.telefono,
            "email_contacto": str(body.email),
            "direccion": body.direccion,
            "ciudad": body.ciudad,
            "descripcion": body.descripcion,
            "estado": EstadoTallerEnum.PENDIENTE,
        },
        db,
        ejecutor_id=user.id,
    )
    u2 = await usuarios_service.get_usuario_by_id(user.id, db)
    await crear_y_enviar_verificacion_email(db, u2)
    return await build_mi_taller_read(taller, u2)


async def build_mi_taller_read(taller: Taller, responsable: Usuario) -> MiTallerRead:
    return MiTallerRead(
        id=taller.id,
        nombre_comercial=taller.nombre_comercial,
        telefono_contacto=taller.telefono_contacto,
        email_contacto=taller.email_contacto,
        direccion=taller.direccion,
        ciudad=taller.ciudad,
        descripcion=taller.descripcion,
        estado=taller.estado,
        created_at=taller.created_at,
        responsable_nombres=responsable.nombres,
        responsable_apellidos=responsable.apellidos,
        responsable_email=responsable.email,
        responsable_telefono=responsable.telefono,
        pendiente_verificacion_email=(responsable.estado == EstadoUsuarioEnum.PENDIENTE),
    )


async def get_mi_taller(usuario_id: int, db: AsyncSession) -> MiTallerRead:
    t_res = await db.execute(select(Taller).where(Taller.usuario_responsable_id == usuario_id))
    taller = t_res.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="No se encontró taller para tu cuenta.")
    user = await usuarios_service.get_usuario_by_id(usuario_id, db)
    return await build_mi_taller_read(taller, user)


async def update_mi_taller(usuario_id: int, body: MiTallerUpdate, db: AsyncSession) -> MiTallerRead:
    t_res = await db.execute(select(Taller).where(Taller.usuario_responsable_id == usuario_id))
    taller = t_res.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="No se encontró taller para tu cuenta.")
    user = await usuarios_service.get_usuario_by_id(usuario_id, db)

    taller_data = body.model_dump(exclude_none=True, exclude={"usuario"})
    if taller_data:
        await talleres_service.update_taller(taller.id, taller_data, db, ejecutor_id=usuario_id)

    if body.usuario:
        udata = body.usuario.model_dump(exclude_none=True)
        if udata:
            if "telefono" in udata:
                other = await db.execute(
                    select(Usuario).where(Usuario.telefono == udata["telefono"], Usuario.id != user.id)
                )
                if other.scalar_one_or_none():
                    raise HTTPException(status_code=409, detail="El teléfono ya está en uso.")
            await usuarios_service.update_usuario(user.id, udata, db, ejecutor_id=usuario_id)

    taller = await talleres_service.get_taller_by_id(taller.id, db)
    user = await usuarios_service.get_usuario_by_id(usuario_id, db)
    return await build_mi_taller_read(taller, user)


async def list_tecnicos_portal(taller_id: int, db: AsyncSession) -> list[TecnicoPortalRead]:
    stmt = (
        select(Tecnico, Usuario, EspecialidadTecnico)
        .join(Usuario, Usuario.id == Tecnico.usuario_id)
        .outerjoin(EspecialidadTecnico, EspecialidadTecnico.id == Tecnico.especialidad_id)
        .where(Tecnico.taller_id == taller_id)
        .order_by(Usuario.apellidos, Usuario.nombres)
    )
    rows = (await db.execute(stmt)).all()
    out: list[TecnicoPortalRead] = []
    for tecnico, usuario, esp in rows:
        out.append(_to_tecnico_read(tecnico, usuario, esp))
    return out


def _to_tecnico_read(
    tecnico: Tecnico,
    usuario: Usuario,
    esp: EspecialidadTecnico | None,
) -> TecnicoPortalRead:
    created = tecnico.created_at.isoformat() if tecnico.created_at else None
    return TecnicoPortalRead(
        id=tecnico.id,
        usuario_id=tecnico.usuario_id,
        taller_id=tecnico.taller_id,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        email=usuario.email,
        telefono=usuario.telefono,
        documento=tecnico.documento_identidad,
        especialidad_id=tecnico.especialidad_id,
        especialidad_nombre=esp.nombre if esp else None,
        disponibilidad=tecnico.disponibilidad,
        estado=tecnico.estado,
        created_at=tecnico.created_at,
        resumen_actividad=f"Alta en el sistema{f' ({created})' if created else ''}.",
    )


async def get_tecnico_portal(tecnico_id: int, taller_id: int, db: AsyncSession) -> TecnicoPortalRead:
    stmt = (
        select(Tecnico, Usuario, EspecialidadTecnico)
        .join(Usuario, Usuario.id == Tecnico.usuario_id)
        .outerjoin(EspecialidadTecnico, EspecialidadTecnico.id == Tecnico.especialidad_id)
        .where(Tecnico.id == tecnico_id, Tecnico.taller_id == taller_id)
    )
    row = (await db.execute(stmt)).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Técnico no encontrado.")
    return _to_tecnico_read(row[0], row[1], row[2])


async def create_tecnico_portal(
    taller_id: int,
    body: TecnicoPortalCreate,
    ejecutor_id: int,
    db: AsyncSession,
) -> TecnicoPortalRead:
    nombres, apellidos = _split_nombre_completo(body.nombre_completo)
    dup_tel = await db.execute(select(Usuario).where(Usuario.telefono == body.telefono))
    if dup_tel.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El teléfono ya está registrado.")

    user = await usuarios_service.create_usuario(
        {
            "nombres": nombres,
            "apellidos": apellidos,
            "email": str(body.email),
            "telefono": body.telefono,
            "password": body.password,
            "username": None,
            "estado": EstadoUsuarioEnum.ACTIVO,
        },
        db,
        ejecutor_id=ejecutor_id,
    )
    rid = await _rol_id_by_nombre(db, "TECNICO")
    await asignar_roles_usuario(user.id, [rid], db)

    t = Tecnico(
        usuario_id=user.id,
        taller_id=taller_id,
        especialidad_id=body.especialidad_id,
        documento_identidad=body.documento,
        disponibilidad=body.disponibilidad,
        estado=body.estado,
        created_at=utc_now_naive(),
        updated_at=utc_now_naive(),
    )
    db.add(t)
    await db.flush()
    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="taller_responsable",
        entidad="tecnicos",
        entidad_id=t.id,
        accion=AccionBitacoraEnum.CREAR,
        descripcion=f"Técnico registrado: {user.email}",
    )
    return await get_tecnico_portal(t.id, taller_id, db)


async def update_tecnico_portal(
    tecnico_id: int,
    taller_id: int,
    body: TecnicoPortalUpdate,
    ejecutor_id: int,
    db: AsyncSession,
) -> TecnicoPortalRead:
    await get_tecnico_portal(tecnico_id, taller_id, db)
    res_t = await db.execute(select(Tecnico).where(Tecnico.id == tecnico_id, Tecnico.taller_id == taller_id))
    tecnico = res_t.scalar_one()

    if body.documento is not None:
        tecnico.documento_identidad = body.documento
    if body.disponibilidad is not None:
        tecnico.disponibilidad = body.disponibilidad
    if body.especialidad_id is not None:
        tecnico.especialidad_id = body.especialidad_id
    if body.estado is not None:
        tecnico.estado = body.estado
    tecnico.updated_at = utc_now_naive()

    user = await usuarios_service.get_usuario_by_id(tecnico.usuario_id, db)
    if body.nombre_completo:
        n, a = _split_nombre_completo(body.nombre_completo)
        user.nombres = n
        user.apellidos = a
    if body.email is not None:
        other = await db.execute(select(Usuario).where(Usuario.email == str(body.email), Usuario.id != user.id))
        if other.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El email ya está en uso.")
        user.email = str(body.email)
    if body.telefono is not None:
        other = await db.execute(
            select(Usuario).where(Usuario.telefono == body.telefono, Usuario.id != user.id)
        )
        if other.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El teléfono ya está en uso.")
        user.telefono = body.telefono
    user.updated_at = utc_now_naive()

    await registrar_accion(
        db=db,
        usuario_id=ejecutor_id,
        modulo="taller_responsable",
        entidad="tecnicos",
        entidad_id=tecnico_id,
        accion=AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Técnico actualizado: {tecnico_id}",
    )
    return await get_tecnico_portal(tecnico_id, taller_id, db)


async def dashboard_taller(usuario_id: int, db: AsyncSession) -> TallerDashboardRead:
    t_res = await db.execute(select(Taller).where(Taller.usuario_responsable_id == usuario_id))
    taller = t_res.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="No se encontró taller para tu cuenta.")
    techs = await talleres_service.get_tecnicos(db, taller_id=taller.id)
    total = len(techs)
    activos = sum(1 for x in techs if x.estado == EstadoTecnicoEnum.ACTIVO)
    if total == 0:
        disp = "Sin técnicos registrados aún."
    else:
        pct = round(100 * activos / total)
        disp = f"{activos} de {total} técnicos activos ({pct}% disponibilidad operativa)."
    return TallerDashboardRead(
        tecnicos_registrados=total,
        tecnicos_activos=activos,
        disponibilidad_general=disp,
        taller_estado=taller.estado,
    )
