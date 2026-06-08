# Servicio — asignación de miembros a tenant (CU44)
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import HTTPException, status

from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.tenants import service as tenants_service
from app.modules.ciclo4.tenants.schemas import (
    AssignmentItemRead,
    AssignmentResultOut,
    TenantMemberTechnicianRead,
    TenantMemberUserRead,
    TenantMemberWorkshopRead,
    TenantMembersRead,
)
from app.modules.talleres_y_tecnicos.talleres.models import Taller, Tecnico


async def listar_members(tenant_id: int, db: AsyncSession) -> TenantMembersRead:
    await tenants_service.get_tenant_o_404(tenant_id, db)

    res_u = await db.execute(
        select(Usuario)
        .where(Usuario.tenant_id == tenant_id)
        .order_by(Usuario.apellidos, Usuario.nombres)
    )
    usuarios = [
        TenantMemberUserRead(
            id=u.id,
            nombres=u.nombres,
            apellidos=u.apellidos,
            email=u.email,
            username=u.username,
        )
        for u in res_u.scalars().all()
    ]

    res_t = await db.execute(
        select(Taller)
        .where(Taller.tenant_id == tenant_id)
        .order_by(Taller.nombre_comercial)
    )
    talleres = [
        TenantMemberWorkshopRead(
            id=t.id,
            nombre_comercial=t.nombre_comercial,
            ciudad=t.ciudad,
            estado=t.estado.value,
            latitud=float(t.latitud) if t.latitud is not None else None,
            longitud=float(t.longitud) if t.longitud is not None else None,
        )
        for t in res_t.scalars().all()
    ]

    res_tc = await db.execute(
        select(Tecnico, Taller.nombre_comercial)
        .join(Taller, Tecnico.taller_id == Taller.id)
        .where(Taller.tenant_id == tenant_id)
        .order_by(Tecnico.id)
    )
    tecnicos = [
        TenantMemberTechnicianRead(
            id=tc.id,
            usuario_id=tc.usuario_id,
            taller_id=tc.taller_id,
            taller_nombre=nombre,
            estado=tc.estado.value,
        )
        for tc, nombre in res_tc.all()
    ]

    return TenantMembersRead(
        tenant_id=tenant_id,
        usuarios=usuarios,
        talleres=talleres,
        tecnicos=tecnicos,
    )


async def _asignar_entidades(
    db: AsyncSession,
    *,
    tenant_id: int,
    usuario_actor_id: int | None,
    entidad_tipo: str,
    items: list[tuple[int, int | None, object]],
) -> tuple[list[AssignmentItemRead], list[int]]:
    assigned: list[AssignmentItemRead] = []
    skipped: list[int] = []

    for entidad_id, tenant_anterior, entidad in items:
        if tenant_anterior == tenant_id:
            skipped.append(entidad_id)
            continue
        if entidad_tipo == "usuario":
            entidad.tenant_id = tenant_id  # type: ignore[attr-defined]
        elif entidad_tipo == "taller":
            entidad.tenant_id = tenant_id  # type: ignore[attr-defined]
        assigned.append(
            AssignmentItemRead(
                id=entidad_id,
                tipo=entidad_tipo,  # type: ignore[arg-type]
                tenant_id_anterior=tenant_anterior,
            )
        )

    if assigned:
        await registrar_accion(
            db,
            "tenants",
            entidad_tipo + "s",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=(
                f"Asignación a tenant_id={tenant_id}: "
                f"{entidad_tipo}s={[a.id for a in assigned]}"
            ),
            usuario_id=usuario_actor_id,
            entidad_id=tenant_id,
        )
    await db.flush()
    return assigned, skipped


async def assign_users(
    tenant_id: int,
    user_ids: list[int],
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    unique_ids = list(dict.fromkeys(user_ids))

    res = await db.execute(select(Usuario).where(Usuario.id.in_(unique_ids)))
    found = {u.id: u for u in res.scalars().all()}
    missing = [uid for uid in unique_ids if uid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuarios no encontrados: {missing}",
        )

    items = [(uid, found[uid].tenant_id, found[uid]) for uid in unique_ids]
    assigned, skipped = await _asignar_entidades(
        db,
        tenant_id=tenant_id,
        usuario_actor_id=usuario_actor_id,
        entidad_tipo="usuario",
        items=items,
    )
    return AssignmentResultOut(tenant_id=tenant_id, assigned=assigned, skipped=skipped)


async def assign_workshops(
    tenant_id: int,
    workshop_ids: list[int],
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    unique_ids = list(dict.fromkeys(workshop_ids))

    res = await db.execute(select(Taller).where(Taller.id.in_(unique_ids)))
    found = {t.id: t for t in res.scalars().all()}
    missing = [wid for wid in unique_ids if wid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Talleres no encontrados: {missing}",
        )

    items = [(wid, found[wid].tenant_id, found[wid]) for wid in unique_ids]
    assigned, skipped = await _asignar_entidades(
        db,
        tenant_id=tenant_id,
        usuario_actor_id=usuario_actor_id,
        entidad_tipo="taller",
        items=items,
    )
    return AssignmentResultOut(tenant_id=tenant_id, assigned=assigned, skipped=skipped)


async def assign_technicians(
    tenant_id: int,
    technician_ids: list[int],
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    unique_ids = list(dict.fromkeys(technician_ids))

    res = await db.execute(
        select(Tecnico)
        .options(selectinload(Tecnico.taller))
        .where(Tecnico.id.in_(unique_ids))
    )
    found = {t.id: t for t in res.scalars().all()}
    missing = [tid for tid in unique_ids if tid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Técnicos no encontrados: {missing}",
        )

    # Cargar usuarios de técnicos
    usuario_ids = [t.usuario_id for t in found.values()]
    res_u = await db.execute(select(Usuario).where(Usuario.id.in_(usuario_ids)))
    usuarios = {u.id: u for u in res_u.scalars().all()}

    assigned: list[AssignmentItemRead] = []
    skipped: list[int] = []

    for tid in unique_ids:
        tecnico = found[tid]
        usuario = usuarios.get(tecnico.usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario del técnico {tid} no encontrado",
            )
        prev = usuario.tenant_id
        if prev == tenant_id and tecnico.taller.tenant_id == tenant_id:
            skipped.append(tid)
            continue
        usuario.tenant_id = tenant_id
        if tecnico.taller.tenant_id != tenant_id:
            tecnico.taller.tenant_id = tenant_id
        assigned.append(
            AssignmentItemRead(id=tid, tipo="tecnico", tenant_id_anterior=prev)
        )

    if assigned:
        await registrar_accion(
            db,
            "tenants",
            "tecnicos",
            AccionBitacoraEnum.ACTUALIZAR,
            descripcion=f"Técnicos asignados a tenant_id={tenant_id}: {[a.id for a in assigned]}",
            usuario_id=usuario_actor_id,
            entidad_id=tenant_id,
        )
    await db.flush()
    return AssignmentResultOut(tenant_id=tenant_id, assigned=assigned, skipped=skipped)


async def patch_user_tenant(
    user_id: int,
    tenant_id: int,
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    res = await db.execute(select(Usuario).where(Usuario.id == user_id))
    usuario = res.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    prev = usuario.tenant_id
    if prev == tenant_id:
        return AssignmentResultOut(
            tenant_id=tenant_id,
            assigned=[],
            skipped=[user_id],
        )
    usuario.tenant_id = tenant_id
    await registrar_accion(
        db,
        "tenants",
        "usuarios",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Usuario {user_id} movido a tenant_id={tenant_id}",
        usuario_id=usuario_actor_id,
        entidad_id=user_id,
    )
    await db.flush()
    return AssignmentResultOut(
        tenant_id=tenant_id,
        assigned=[AssignmentItemRead(id=user_id, tipo="usuario", tenant_id_anterior=prev)],
    )


async def patch_workshop_tenant(
    workshop_id: int,
    tenant_id: int,
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    res = await db.execute(select(Taller).where(Taller.id == workshop_id))
    taller = res.scalar_one_or_none()
    if taller is None:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    prev = taller.tenant_id
    if prev == tenant_id:
        return AssignmentResultOut(tenant_id=tenant_id, assigned=[], skipped=[workshop_id])
    taller.tenant_id = tenant_id
    await registrar_accion(
        db,
        "tenants",
        "talleres",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Taller {workshop_id} movido a tenant_id={tenant_id}",
        usuario_id=usuario_actor_id,
        entidad_id=workshop_id,
    )
    await db.flush()
    return AssignmentResultOut(
        tenant_id=tenant_id,
        assigned=[
            AssignmentItemRead(id=workshop_id, tipo="taller", tenant_id_anterior=prev)
        ],
    )


async def patch_technician_tenant(
    technician_id: int,
    tenant_id: int,
    db: AsyncSession,
    *,
    usuario_actor_id: int | None = None,
) -> AssignmentResultOut:
    await tenants_service.get_tenant_o_404(tenant_id, db)
    res = await db.execute(
        select(Tecnico)
        .options(selectinload(Tecnico.taller))
        .where(Tecnico.id == technician_id)
    )
    tecnico = res.scalar_one_or_none()
    if tecnico is None:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")

    res_u = await db.execute(select(Usuario).where(Usuario.id == tecnico.usuario_id))
    usuario = res_u.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario del técnico no encontrado")

    prev = usuario.tenant_id
    if prev == tenant_id and tecnico.taller.tenant_id == tenant_id:
        return AssignmentResultOut(
            tenant_id=tenant_id, assigned=[], skipped=[technician_id]
        )

    usuario.tenant_id = tenant_id
    if tecnico.taller.tenant_id != tenant_id:
        tecnico.taller.tenant_id = tenant_id

    await registrar_accion(
        db,
        "tenants",
        "tecnicos",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Técnico {technician_id} movido a tenant_id={tenant_id}",
        usuario_id=usuario_actor_id,
        entidad_id=technician_id,
    )
    await db.flush()
    return AssignmentResultOut(
        tenant_id=tenant_id,
        assigned=[
            AssignmentItemRead(
                id=technician_id, tipo="tecnico", tenant_id_anterior=prev
            )
        ],
    )
