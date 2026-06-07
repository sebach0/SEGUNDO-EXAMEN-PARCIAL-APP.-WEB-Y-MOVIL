# Bandeja taller: listado, detalle, disponibilidad, aceptar, rechazar.
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.incidentes.emergencias.solicitud_lifecycle import aplicar_timestamps_por_estado
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
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "La aceptación directa fue reemplazada por el marketplace de cotizaciones. "
            "Enviá una cotización con precio, servicios y ETA desde el módulo Cotizaciones."
        ),
    )
