# Alta, listado, detalle, seguimiento y texto de solicitudes (cliente).
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.ai.services.post_create import enrich_solicitud_ai_after_create
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias import repository
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum
from app.modules.incidentes.emergencias.schemas import (
    SolicitudEmergenciaCreateIn,
    SolicitudEmergenciaDetailRead,
    SolicitudEmergenciaRead,
    SolicitudEmergenciaUpdateTextoIn,
    SolicitudSeguimientoRead,
    UbicacionTecnicoCompartidaRead,
)
from app.modules.atencion.taller_emergencias.repository import insert_bandeja_pendiente_por_cada_taller
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import helpers


async def crear_solicitud(
    user: Usuario,
    cliente_id: int,
    body: SolicitudEmergenciaCreateIn,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    v = await repository.get_vehiculo_if_cliente(db, vehiculo_id=body.vehiculo_id, cliente_id=cliente_id)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado o no pertenece a tu cuenta.",
        )

    now = utc_now_naive()
    desc: str | None
    if body.descripcion_texto is None:
        desc = None
    else:
        st = body.descripcion_texto.strip()
        desc = st if st else None

    sol = await repository.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=body.vehiculo_id,
        descripcion_texto=desc,
        estado=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        created_at=now,
        updated_at=now,
    )
    await repository.insert_historial_estado(
        db,
        solicitud_id=sol.id,
        estado_anterior=None,
        estado_nuevo=sol.estado,
        usuario_id=user.id,
        observacion="Alta de solicitud",
        created_at=now,
    )

    if body.ubicacion_inicial is not None:
        await helpers.add_ubicacion_internal(db, sol, body.ubicacion_inicial, now)

    await insert_bandeja_pendiente_por_cada_taller(
        db, solicitud_id=sol.id, creado_at=now
    )

    await registrar_accion(
        db,
        "emergencias",
        "solicitudes_emergencia",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Solicitud emergencia vehículo_id={body.vehiculo_id}",
        usuario_id=user.id,
        entidad_id=sol.id,
    )

    await enrich_solicitud_ai_after_create(db, solicitud_id=sol.id, cliente_id=cliente_id)

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=sol.id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)


async def listar_solicitudes(
    cliente_id: int,
    db: AsyncSession,
    *,
    limit: int = 100,
) -> list[SolicitudEmergenciaRead]:
    rows = await repository.list_solicitudes_cliente(db, cliente_id=cliente_id, limit=limit)
    return [SolicitudEmergenciaRead.model_validate(r) for r in rows]


async def obtener_detalle(
    cliente_id: int,
    solicitud_id: int,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    s = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return helpers.to_detail(s)


async def obtener_seguimiento(
    cliente_id: int,
    solicitud_id: int,
    db: AsyncSession,
) -> SolicitudSeguimientoRead:
    """CU16–CU18: estado, historial, taller/técnico asignados y ETA (solo solicitudes propias)."""
    s = await repository.get_solicitud_seguimiento_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id
    )
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return helpers.to_seguimiento(s)


async def actualizar_texto(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    body: SolicitudEmergenciaUpdateTextoIn,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    s = await repository.get_solicitud_for_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    helpers.require_registrada(s)

    patch = body.model_dump(exclude_unset=True)
    if "descripcion_texto" not in patch:
        s2 = await repository.get_solicitud_for_cliente(
            db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
        )
        assert s2 is not None
        return helpers.to_detail(s2)

    raw = patch["descripcion_texto"]
    if raw is None:
        s.descripcion_texto = None
    else:
        st = raw.strip()
        s.descripcion_texto = st if st else None
    s.updated_at = utc_now_naive()

    await registrar_accion(
        db,
        "emergencias",
        "solicitudes_emergencia",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion="Actualización de texto adicional",
        usuario_id=user.id,
        entidad_id=s.id,
    )

    await enrich_solicitud_ai_after_create(db, solicitud_id=solicitud_id, cliente_id=cliente_id)

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)


async def obtener_ubicacion_tecnico_compartida_cliente(
    cliente_id: int,
    solicitud_id: int,
    db: AsyncSession,
) -> UbicacionTecnicoCompartidaRead:
    s = await repository.get_solicitud_for_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    if s.tecnico_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aún no hay técnico asignado a esta solicitud.",
        )
    if s.tecnico_ult_ubicacion_at is None or s.tecnico_ult_latitud is None or s.tecnico_ult_longitud is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El técnico aún no ha compartido su ubicación.",
        )
    return UbicacionTecnicoCompartidaRead(
        solicitud_id=s.id,
        latitud=s.tecnico_ult_latitud,
        longitud=s.tecnico_ult_longitud,
        precision_metros=s.tecnico_ult_precision_metros,
        actualizado_at=s.tecnico_ult_ubicacion_at,
    )
