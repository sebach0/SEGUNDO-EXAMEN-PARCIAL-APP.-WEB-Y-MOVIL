from __future__ import annotations

from decimal import Decimal

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
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from .. import repository
from ..schemas import ActualizarEstadoServicioIn, ServicioAsignadoRead
from .acceso import get_tecnico_row_for_usuario


def _etiqueta_estado_cliente(nuevo: EstadoSolicitudSeguimientoEnum) -> str:
    return {
        EstadoSolicitudSeguimientoEnum.EN_CAMINO: "el técnico va en camino",
        EstadoSolicitudSeguimientoEnum.EN_ATENCION: "atención en curso",
        EstadoSolicitudSeguimientoEnum.FINALIZADA: "el servicio fue finalizado",
    }.get(
        nuevo,
        f"estado: {nuevo.value.replace('_', ' ').lower()}",
    )


_ALLOWED_TRANSITIONS: dict[
    EstadoSolicitudSeguimientoEnum, frozenset[EstadoSolicitudSeguimientoEnum]
] = {
    EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO: frozenset({EstadoSolicitudSeguimientoEnum.EN_CAMINO}),
    EstadoSolicitudSeguimientoEnum.EN_CAMINO: frozenset({EstadoSolicitudSeguimientoEnum.EN_ATENCION}),
    EstadoSolicitudSeguimientoEnum.EN_ATENCION: frozenset({EstadoSolicitudSeguimientoEnum.FINALIZADA}),
}


def _estado_terminal(estado: EstadoSolicitudSeguimientoEnum) -> bool:
    return estado in (
        EstadoSolicitudSeguimientoEnum.FINALIZADA,
        EstadoSolicitudSeguimientoEnum.CANCELADA,
    )


async def actualizar_estado_servicio(
    user: Usuario, solicitud_id: int, body: ActualizarEstadoServicioIn, db: AsyncSession
) -> ServicioAsignadoRead:
    t = await get_tecnico_row_for_usuario(user.id, db)
    now = utc_now_naive()
    obs = body.observacion.strip() if body.observacion else None
    obs = obs if obs else None

    res = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .with_for_update()
    )
    se = res.scalar_one_or_none()
    if se is None or se.tecnico_id != t.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada.",
        )
    if _estado_terminal(se.estado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya está cerrada.",
        )

    permitidos = _ALLOWED_TRANSITIONS.get(se.estado, frozenset())
    if body.nuevo_estado not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede pasar de {se.estado.value} a {body.nuevo_estado.value}.",
        )

    estado_anterior = se.estado
    se.estado = body.nuevo_estado
    se.updated_at = now
    if body.nuevo_estado == EstadoSolicitudSeguimientoEnum.EN_CAMINO and se.tiempo_estimado_min is None:
        se.tiempo_estimado_min = 20
    if body.nuevo_estado == EstadoSolicitudSeguimientoEnum.EN_ATENCION:
        se.presupuesto_bob = body.presupuesto_bob
        se.presupuesto_registrado_at = now
    if body.nuevo_estado == EstadoSolicitudSeguimientoEnum.FINALIZADA:
        se.finalizada_at = now

    await emergencias_repository.insert_historial_estado(
        db,
        solicitud_id=se.id,
        estado_anterior=estado_anterior,
        estado_nuevo=body.nuevo_estado,
        usuario_id=user.id,
        observacion=obs or f"Actualización de estado: {body.nuevo_estado.value}",
        created_at=now,
    )

    await registrar_accion(
        db,
        "tecnico",
        "solicitudes_emergencia",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"solicitud_id={solicitud_id} estado={body.nuevo_estado.value}",
        usuario_id=user.id,
        entidad_id=solicitud_id,
    )

    etiqueta = _etiqueta_estado_cliente(body.nuevo_estado)
    monto_txt: str | None = None
    if body.nuevo_estado == EstadoSolicitudSeguimientoEnum.EN_ATENCION and body.presupuesto_bob is not None:
        monto_txt = f"{body.presupuesto_bob.quantize(Decimal('0.01'))} Bs."
    mensaje_cliente = (
        f"Te informamos: {etiqueta}. Presupuesto indicado: {monto_txt}."
        if monto_txt
        else f"Te informamos: {etiqueta}."
    )
    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=se,
        tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
        titulo="Estado de tu servicio",
        mensaje=mensaje_cliente,
    )

    row = await repository.get_servicio_asignado_detalle(db, solicitud_id=solicitud_id, tecnico_id=t.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    return ServicioAsignadoRead.model_validate(row)
