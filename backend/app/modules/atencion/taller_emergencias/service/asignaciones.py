# Asignación y reasignación de técnico (CU28) e historial de asignaciones.
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias import repository as emergencias_repository
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, SolicitudEmergencia
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notificaciones_service
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.atencion.taller_emergencias import repository
from app.modules.atencion.taller_emergencias.models import EstadoAsignacionTecnicoEnum
from app.modules.atencion.taller_emergencias.schemas import AsignacionTecnicoRead, AsignarTecnicoIn, AsignarTecnicoOut
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import helpers


async def _get_solicitud_taller_o_none(
    db: AsyncSession, *, solicitud_id: int, taller_id: int
) -> SolicitudEmergencia | None:
    res = await db.execute(
        select(SolicitudEmergencia).where(
            SolicitudEmergencia.id == solicitud_id,
            SolicitudEmergencia.taller_id == taller_id,
        )
    )
    return res.scalar_one_or_none()


async def listar_asignaciones_tecnico(
    taller_id: int, solicitud_id: int, db: AsyncSession
) -> list[AsignacionTecnicoRead]:
    se = await _get_solicitud_taller_o_none(db, solicitud_id=solicitud_id, taller_id=taller_id)
    if se is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    rows = await repository.list_asignaciones_tecnico_por_solicitud_taller(
        db, solicitud_id=solicitud_id, taller_id=taller_id
    )
    return [helpers.to_asignacion_read(r) for r in rows]


async def asignar_tecnico_a_solicitud(
    user: Usuario,
    taller_id: int,
    solicitud_id: int,
    body: AsignarTecnicoIn,
    db: AsyncSession,
) -> AsignarTecnicoOut:
    now = utc_now_naive()
    obs: str | None = None
    if body.observacion is not None:
        st_obs = body.observacion.strip()
        obs = st_obs if st_obs else None

    res_se = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .with_for_update()
    )
    se = res_se.scalar_one_or_none()
    if se is None or se.taller_id != taller_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")

    if helpers.estado_terminal_solicitud(se.estado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya no admite asignación de técnico.",
        )
    if se.estado not in helpers.ESTADOS_PERMITE_ASIGNAR_TECNICO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud no admite asignación de técnico en su estado actual.",
        )

    tecnico = await repository.get_tecnico_del_taller_activo(
        db, tecnico_id=body.tecnico_id, taller_id=taller_id
    )
    if tecnico is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Técnico no encontrado, inactivo o no pertenece a este taller.",
        )
    if not helpers.tecnico_disponible_para_asignar(tecnico):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El técnico no está disponible para asignación.",
        )

    if se.tecnico_id == body.tecnico_id and se.estado == EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO:
        existente = await repository.find_asignacion_activa_mismo_tecnico(
            db, solicitud_id=solicitud_id, taller_id=taller_id, tecnico_id=body.tecnico_id
        )
        if existente is not None:
            return helpers.to_asignar_out(se, existente)

    if se.tecnico_id is not None and se.tecnico_id != body.tecnico_id:
        await repository.marcar_asignaciones_activas_como_reasignado(
            db, solicitud_id=solicitud_id, taller_id=taller_id
        )

    estado_antes = se.estado
    tecnico_previo = se.tecnico_id
    se.tecnico_id = body.tecnico_id
    se.tecnico_asignado_at = now
    se.updated_at = now
    if body.tiempo_estimado_min is not None:
        se.tiempo_estimado_min = body.tiempo_estimado_min

    if estado_antes == EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO:
        se.estado = EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO
        msg_hist = (
            "Asignación de técnico"
            if tecnico_previo is None
            else "Cambio de técnico"
        )
        await emergencias_repository.insert_historial_estado(
            db,
            solicitud_id=se.id,
            estado_anterior=estado_antes,
            estado_nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
            usuario_id=user.id,
            observacion=msg_hist,
            created_at=now,
        )
    elif estado_antes == EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO:
        await emergencias_repository.insert_historial_estado(
            db,
            solicitud_id=se.id,
            estado_anterior=estado_antes,
            estado_nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
            usuario_id=user.id,
            observacion="Reasignación de técnico",
            created_at=now,
        )

    asignacion = await repository.insert_asignacion_tecnico(
        db,
        solicitud_id=solicitud_id,
        taller_id=taller_id,
        tecnico_id=body.tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=user.id,
        observacion=obs,
        created_at=now,
    )

    await registrar_accion(
        db,
        "taller_emergencias",
        "solicitud_asignaciones_tecnico",
        AccionBitacoraEnum.CREAR,
        descripcion=f"solicitud_id={solicitud_id} tecnico_id={body.tecnico_id}",
        usuario_id=user.id,
        entidad_id=asignacion.id,
    )

    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=se,
        tipo=TipoNotificacionEnum.TECNICO_ASIGNADO,
        titulo="Técnico asignado",
        mensaje="Se asignó un técnico a tu emergencia. Sigue el avance en la app.",
    )
    await notificaciones_service.notificar_tecnico_solicitud_emergencia(
        db,
        solicitud=se,
        tipo=TipoNotificacionEnum.TECNICO_ASIGNADO,
        titulo="Nueva asignación",
        mensaje=f"Te asignaron la emergencia #{solicitud_id}. Abre la app para ver detalles.",
    )

    return helpers.to_asignar_out(se, asignacion)
