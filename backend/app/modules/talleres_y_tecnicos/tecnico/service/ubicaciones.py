from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias import repository as emergencias_repository
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)
from app.modules.incidentes.emergencias.eta_service import evaluar_y_notificar_retraso
from app.modules.incidentes.emergencias.schemas import UbicacionCreateIn, UbicacionTecnicoCompartidaRead
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from .. import repository
from ..schemas import UbicacionClienteActualRead
from .acceso import get_tecnico_row_for_usuario


def _estado_terminal(estado: EstadoSolicitudSeguimientoEnum) -> bool:
    return estado in (
        EstadoSolicitudSeguimientoEnum.FINALIZADA,
        EstadoSolicitudSeguimientoEnum.CANCELADA,
    )


async def obtener_ubicacion_cliente(
    user: Usuario, solicitud_id: int, db: AsyncSession
) -> UbicacionClienteActualRead:
    t = await get_tecnico_row_for_usuario(user.id, db)
    row = await repository.get_ubicacion_actual_para_solicitud_tecnico(
        db, solicitud_id=solicitud_id, tecnico_id=t.id
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no disponible o solicitud no asignada a tu cuenta.",
        )
    return UbicacionClienteActualRead.model_validate(row)


async def compartir_ubicacion_tecnico(
    user: Usuario, solicitud_id: int, body: UbicacionCreateIn, db: AsyncSession
) -> UbicacionTecnicoCompartidaRead:
    t = await get_tecnico_row_for_usuario(user.id, db)
    res = await db.execute(select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id))
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

    now = utc_now_naive()
    await emergencias_repository.update_tecnico_ultima_ubicacion(
        db,
        solicitud_id=solicitud_id,
        latitud=body.latitud,
        longitud=body.longitud,
        precision_metros=body.precision_metros,
        ubicacion_at=now,
    )
    await evaluar_y_notificar_retraso(db, se)

    await registrar_accion(
        db,
        "tecnico",
        "solicitudes_emergencia",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"solicitud_id={solicitud_id} tecnico_ubicacion_compartida",
        usuario_id=user.id,
        entidad_id=solicitud_id,
    )

    return UbicacionTecnicoCompartidaRead(
        solicitud_id=solicitud_id,
        latitud=body.latitud,
        longitud=body.longitud,
        precision_metros=body.precision_metros,
        actualizado_at=now,
    )
