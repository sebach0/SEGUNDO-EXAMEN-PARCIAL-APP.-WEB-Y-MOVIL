# Alta, listado, detalle, seguimiento y texto de solicitudes (cliente).
from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

_log = logging.getLogger(__name__)

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
from app.modules.atencion.taller_emergencias.repository import insert_bandeja_pendiente_por_talleres
from app.modules.ciclo4.deps import _DEFAULT_TENANT_ID
from app.modules.incidentes.emergencias.solicitud_lifecycle import init_reportado_en, marcar_cancelacion
from app.modules.incidentes.emergencias.taller_elegibilidad import listar_taller_ids_elegibles
from app.modules.incidentes.emergencias.eta_service import evaluar_y_notificar_retraso
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import helpers


async def _post_create_pipeline(
    db: AsyncSession,
    *,
    user: Usuario,
    cliente_id: int,
    sol,
    vehiculo_id: int,
    now,
    bitacora_desc: str,
) -> None:
    await enrich_solicitud_ai_after_create(db, solicitud_id=sol.id, cliente_id=cliente_id)
    await db.refresh(sol)

    taller_ids = await listar_taller_ids_elegibles(
        db,
        tenant_id=sol.tenant_id,
        ai_payload=sol.ai_payload,
    )
    if not taller_ids:
        from app.modules.atencion.taller_emergencias.repository import insert_bandeja_pendiente_por_cada_taller

        await insert_bandeja_pendiente_por_cada_taller(db, solicitud_id=sol.id, creado_at=now)
    else:
        await insert_bandeja_pendiente_por_talleres(
            db, solicitud_id=sol.id, taller_ids=taller_ids, creado_at=now
        )

    await registrar_accion(
        db,
        "emergencias",
        "solicitudes_emergencia",
        AccionBitacoraEnum.CREAR,
        descripcion=bitacora_desc,
        usuario_id=user.id,
        entidad_id=sol.id,
    )


async def _post_create_pipeline_bg(
    *,
    user_id: int,
    user_tenant_id: int | None,
    cliente_id: int,
    sol_id: int,
    sol_tenant_id: int | None,
    vehiculo_id: int,
    now,
    bitacora_desc: str,
) -> None:
    """Ejecuta el pipeline IA + bandeja en una sesión DB propia (para background task)."""
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            from app.modules.incidentes.emergencias import repository as _repo
            sol = await _repo.get_solicitud_for_cliente(db, solicitud_id=sol_id, cliente_id=cliente_id)
            if sol is None:
                return

            await enrich_solicitud_ai_after_create(db, solicitud_id=sol_id, cliente_id=cliente_id)
            await db.refresh(sol)

            taller_ids = await listar_taller_ids_elegibles(
                db,
                tenant_id=sol.tenant_id,
                ai_payload=sol.ai_payload,
            )
            if not taller_ids:
                from sqlalchemy import select as _sel
                from app.modules.talleres_y_tecnicos.talleres.models import Taller as _T, EstadoTallerEnum as _ETE
                _res = await db.execute(_sel(_T.id).where(_T.estado == _ETE.ACTIVO))
                taller_ids = [r[0] for r in _res.all()]

            await insert_bandeja_pendiente_por_talleres(
                db, solicitud_id=sol_id, taller_ids=taller_ids, creado_at=now
            )

            # Notificar en tiempo real a talleres y admin
            try:
                from app.modules.ciclo4.websocket.manager import manager as _ws_manager
                for _tid in taller_ids:
                    await _ws_manager.broadcast_to_taller(
                        taller_id=_tid,
                        event_type="BANDEJA_ACTUALIZADA",
                        message=f"Nueva solicitud #{sol_id} disponible",
                        payload={"solicitud_id": sol_id},
                    )
                await _ws_manager.broadcast_to_admin(
                    event_type="NUEVA_SOLICITUD",
                    message=f"Nueva solicitud de emergencia #{sol_id}",
                    payload={"solicitud_id": sol_id},
                )
            except Exception:
                _log.exception("Error al notificar vía WebSocket sol_id=%s", sol_id)

            await registrar_accion(
                db,
                "emergencias",
                "solicitudes_emergencia",
                AccionBitacoraEnum.CREAR,
                descripcion=bitacora_desc,
                usuario_id=user_id,
                entidad_id=sol_id,
            )
            await db.commit()
    except Exception:
        _log.exception("Error en pipeline AI background sol_id=%s", sol_id)


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
        tenant_id=user.tenant_id or _DEFAULT_TENANT_ID,
    )
    init_reportado_en(sol, now)
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

    await db.commit()

    # Pipeline IA y bandeja en background para no bloquear la respuesta al cliente.
    asyncio.create_task(
        _post_create_pipeline_bg(
            user_id=user.id,
            user_tenant_id=user.tenant_id,
            cliente_id=cliente_id,
            sol_id=sol.id,
            sol_tenant_id=sol.tenant_id,
            vehiculo_id=body.vehiculo_id,
            now=now,
            bitacora_desc=f"Solicitud emergencia vehículo_id={body.vehiculo_id}",
        )
    )

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
    await evaluar_y_notificar_retraso(db, s)
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


async def cancelar_solicitud(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    motivo: str,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    """CU — Cancelación de solicitud por el cliente. Notifica al taller/técnico asignado."""
    s = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id
    )
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")

    estados_cancelables = {
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
        EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.EN_CAMINO,
    }
    if s.estado not in estados_cancelables:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede cancelar en estado '{s.estado.value}'.",
        )

    estado_anterior = s.estado
    now = utc_now_naive()
    marcar_cancelacion(
        s,
        usuario_id=user.id,
        motivo=motivo,
        now=now,
        estado_anterior=estado_anterior,
    )

    await repository.insert_historial_estado(
        db,
        solicitud_id=s.id,
        estado_anterior=estado_anterior,
        estado_nuevo=EstadoSolicitudSeguimientoEnum.CANCELADA,
        usuario_id=user.id,
        observacion=f"Cancelado por cliente. Motivo: {motivo.strip()}",
        created_at=now,
    )

    await registrar_accion(
        db,
        "emergencias",
        "solicitudes_emergencia",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Solicitud cancelada por cliente. Motivo: {motivo.strip()}",
        usuario_id=user.id,
        entidad_id=s.id,
    )

    if s.tecnico_id is not None:
        from app.modules.atencion.taller_emergencias.service.asignaciones import (
            liberar_tecnico_si_sin_servicios,
        )

        await liberar_tecnico_si_sin_servicios(db, s.tecnico_id, now)

    # Notificar al taller asignado (si hay)
    if s.taller_id is not None:
        from app.modules.comunicacion_y_notificaciones.notificaciones import service as notif_service
        from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
        await notif_service.notificar_taller_responsable_solicitud(
            db,
            solicitud=s,
            tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
            titulo="Solicitud cancelada",
            mensaje=(
                f"El cliente canceló la solicitud #{s.id}. "
                f"Motivo: {motivo.strip()}"
            ),
        )
        if s.tecnico_id is not None:
            await notif_service.notificar_tecnico_solicitud_emergencia(
                db,
                solicitud=s,
                tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
                titulo="Solicitud cancelada",
                mensaje=f"El cliente canceló la solicitud #{s.id}.",
            )

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)
