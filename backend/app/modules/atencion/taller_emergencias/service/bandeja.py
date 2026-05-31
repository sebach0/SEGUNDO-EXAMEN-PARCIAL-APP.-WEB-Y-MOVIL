# Bandeja taller: listado, detalle, disponibilidad, aceptar, rechazar.
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notificaciones_service
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.atencion.taller_emergencias import repository
from app.modules.atencion.taller_emergencias.models import EstadoBandejaTallerEnum
from app.modules.atencion.taller_emergencias.schemas import (
    BandejaIncidenteBaseRead,
    RechazarBandejaIn,
    SolicitudBandejaDetalleRead,
    TallerDisponibilidadRead,
    TallerDisponibilidadUpdateIn,
)
from . import helpers
from app.modules.acceso_y_administracion.usuarios.models import Usuario


async def listar_disponibles(taller_id: int, db: AsyncSession) -> list[BandejaIncidenteBaseRead]:
    rows = await repository.list_bandeja_pendiente_por_taller(db, taller_id=taller_id)
    return [helpers.row_to_list_item(r) for r in rows]


async def obtener_detalle_bandeja(
    taller_id: int, bandeja_id: int, db: AsyncSession
) -> SolicitudBandejaDetalleRead:
    row = await repository.get_bandeja_detalle_por_taller(db, bandeja_id=bandeja_id, taller_id=taller_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entrada de bandeja no encontrada"
        )
    evs = await repository.list_evidencias_por_solicitud(db, solicitud_id=row["solicitud_id"])
    return helpers.row_to_detalle(row, evs)


async def obtener_disponibilidad(taller_id: int, db: AsyncSession) -> TallerDisponibilidadRead:
    row = await helpers.ensure_disponibilidad(db, taller_id)
    return TallerDisponibilidadRead(
        taller_id=row.taller_id,
        acepta_nuevas_solicitudes=row.acepta_nuevas_solicitudes,
        capacidad_maxima_diaria=row.capacidad_maxima_diaria,
        servicios_activos=row.servicios_activos,
        observacion=row.observacion,
        updated_at=row.updated_at,
        updated_by_usuario_id=row.updated_by_usuario_id,
    )


async def actualizar_disponibilidad(
    user: Usuario, taller_id: int, body: TallerDisponibilidadUpdateIn, db: AsyncSession
) -> TallerDisponibilidadRead:
    row = await helpers.ensure_disponibilidad(db, taller_id)
    now = utc_now_naive()
    patch = body.model_dump(exclude_unset=True)
    await repository.update_disponibilidad(
        db,
        row=row,
        acepta_nuevas_solicitudes=patch.get("acepta_nuevas_solicitudes"),
        capacidad_maxima_diaria=patch.get("capacidad_maxima_diaria"),
        observacion=patch.get("observacion"),
        updated_by_usuario_id=user.id,
        updated_at=now,
    )
    await registrar_accion(
        db,
        "taller_emergencias",
        "taller_disponibilidad",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"taller_id={taller_id}",
        usuario_id=user.id,
        entidad_id=row.id,
    )
    return await obtener_disponibilidad(taller_id, db)


async def rechazar_solicitud(
    user: Usuario,
    taller_id: int,
    bandeja_id: int,
    body: RechazarBandejaIn,
    db: AsyncSession,
) -> SolicitudBandejaDetalleRead:
    st = body.motivo_rechazo.strip()
    now = utc_now_naive()
    affected = await repository.marcar_bandeja(
        db,
        bandeja_id=bandeja_id,
        taller_id=taller_id,
        estado=EstadoBandejaTallerEnum.RECHAZADA,
        respondido_at=now,
        motivo_rechazo=st,
    )
    if affected == 0:
        b = await repository.get_bandeja_row(db, bandeja_id=bandeja_id, taller_id=taller_id)
        if b is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Entrada de bandeja no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya no está pendiente de respuesta.",
        )
    await registrar_accion(
        db,
        "taller_emergencias",
        "solicitud_taller_bandeja",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Rechazo bandeja_id={bandeja_id} taller_id={taller_id}",
        usuario_id=user.id,
        entidad_id=bandeja_id,
    )
    b_row = await repository.get_bandeja_row(db, bandeja_id=bandeja_id, taller_id=taller_id)
    if b_row is not None:
        se_r = await db.execute(
            select(SolicitudEmergencia).where(SolicitudEmergencia.id == b_row.solicitud_id)
        )
        if (se_n := se_r.scalar_one_or_none()) is not None:
            await notificaciones_service.notificar_cliente_solicitud_emergencia(
                db,
                solicitud=se_n,
                tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
                titulo="Actualización de emergencia",
                mensaje="Un taller no pudo aceptar tu solicitud. Revisa el estado de tu caso en la app.",
            )
    return await obtener_detalle_bandeja(taller_id, bandeja_id, db)


async def aceptar_solicitud(
    user: Usuario,
    taller_id: int,
    bandeja_id: int,
    db: AsyncSession,
) -> SolicitudBandejaDetalleRead:
    from app.modules.incidentes.emergencias import repository as emergencias_repository
    from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum

    now = utc_now_naive()
    bandeja = await repository.get_bandeja_row(db, bandeja_id=bandeja_id, taller_id=taller_id)
    if bandeja is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entrada de bandeja no encontrada"
        )

    if bandeja.estado == EstadoBandejaTallerEnum.ACEPTADA:
        return await obtener_detalle_bandeja(taller_id, bandeja_id, db)
    if bandeja.estado != EstadoBandejaTallerEnum.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya no está pendiente de respuesta.",
        )

    res_se = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == bandeja.solicitud_id)
        .with_for_update()
    )
    se = res_se.scalar_one_or_none()
    if se is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada"
        )
    if helpers.estado_terminal_solicitud(se.estado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya no admite asignación de taller.",
        )
    if se.taller_id is not None and se.taller_id != taller_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue asignada a otro taller.",
        )

    disp = await helpers.ensure_disponibilidad(db, taller_id)
    if not disp.acepta_nuevas_solicitudes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El taller no acepta nuevas solicitudes en este momento.",
        )
    if disp.servicios_activos >= disp.capacidad_maxima_diaria:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Capacidad máxima alcanzada; no se pueden aceptar más servicios.",
        )

    affected = await repository.marcar_bandeja(
        db,
        bandeja_id=bandeja_id,
        taller_id=taller_id,
        estado=EstadoBandejaTallerEnum.ACEPTADA,
        respondido_at=now,
    )
    if affected == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya no está pendiente de respuesta.",
        )

    await repository.expirar_otras_bandeja_pendientes(
        db,
        solicitud_id=bandeja.solicitud_id,
        bandeja_ganadora_id=bandeja_id,
        respondido_at=now,
    )

    estado_anterior = se.estado
    se.taller_id = taller_id
    if estado_anterior in (
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
    ):
        se.estado = EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO
        await emergencias_repository.insert_historial_estado(
            db,
            solicitud_id=se.id,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
            usuario_id=user.id,
            observacion="Taller acepta asistencia",
            created_at=now,
        )
    se.updated_at = now

    disp.servicios_activos = int(disp.servicios_activos) + 1
    disp.updated_by_usuario_id = user.id
    disp.updated_at = now

    await registrar_accion(
        db,
        "taller_emergencias",
        "solicitud_taller_bandeja",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Aceptación bandeja_id={bandeja_id} solicitud_id={bandeja.solicitud_id}",
        usuario_id=user.id,
        entidad_id=bandeja_id,
    )

    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=se,
        tipo=TipoNotificacionEnum.TALLER_ASIGNADO,
        titulo="Taller asignado",
        mensaje="Un taller aceptó atender tu emergencia. Puedes ver el detalle en la app.",
    )

    return await obtener_detalle_bandeja(taller_id, bandeja_id, db)
