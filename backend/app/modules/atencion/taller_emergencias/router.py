# API portal taller — emergencias (ciclo 3 fase 1: bandeja + disponibilidad)
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.timeutil import utc_now_naive
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, SolicitudEmergencia
from app.modules.incidentes.emergencias.solicitud_lifecycle import aplicar_timestamps_por_estado
from app.modules.ciclo4.websocket.manager import manager as ws_manager
from app.modules.talleres_y_tecnicos.taller_responsable.router import require_taller_responsable
from app.modules.talleres_y_tecnicos.talleres.models import Taller
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import service
from .schemas import (
    AsignacionTecnicoRead,
    AsignarTecnicoIn,
    AsignarTecnicoOut,
    BandejaIncidenteBaseRead,
    ComisionTallerRead,
    HistorialAtencionRead,
    RechazarBandejaIn,
    ReporteTallerDashboardRead,
    ResumenComisionesRead,
    SolicitudBandejaDetalleRead,
    TallerDisponibilidadRead,
    TallerDisponibilidadUpdateIn,
)

router = APIRouter(prefix="/app/taller/emergencias", tags=["Emergencias (taller)"])


@router.get(
    "/bandeja/disponibles",
    response_model=list[BandejaIncidenteBaseRead],
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def listar_bandeja_disponibles(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Solicitudes PENDIENTES en la bandeja del taller (vista operativa)."""
    _, taller = ctx
    return await service.listar_disponibles(taller.id, db)


@router.get(
    "/bandeja/{bandeja_id}",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def detalle_bandeja(
    bandeja_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU25 — información estructurada del incidente para una fila de bandeja."""
    _, taller = ctx
    return await service.obtener_detalle_bandeja(taller.id, bandeja_id, db)


@router.post(
    "/bandeja/{bandeja_id}/aceptar",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:aceptar"))],
)
async def aceptar_bandeja(
    bandeja_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU26 — aceptar asistencia; actualiza solicitud y expira otras bandejas pendientes."""
    user, taller = ctx
    return await service.aceptar_solicitud(user, taller.id, bandeja_id, db)


@router.post(
    "/bandeja/{bandeja_id}/rechazar",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:rechazar"))],
)
async def rechazar_bandeja(
    bandeja_id: int,
    body: RechazarBandejaIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU27 — rechazar con motivo."""
    user, taller = ctx
    return await service.rechazar_solicitud(user, taller.id, bandeja_id, body, db)


@router.get(
    "/disponibilidad",
    response_model=TallerDisponibilidadRead,
    dependencies=[Depends(require_permission("disponibilidad:gestionar"))],
)
async def get_disponibilidad(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU29 — lectura (crea fila por defecto si aún no existe)."""
    _, taller = ctx
    return await service.obtener_disponibilidad(taller.id, db)


@router.put(
    "/disponibilidad",
    response_model=TallerDisponibilidadRead,
    dependencies=[Depends(require_permission("disponibilidad:gestionar"))],
    status_code=status.HTTP_200_OK,
)
async def put_disponibilidad(
    body: TallerDisponibilidadUpdateIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU29 — actualizar banderas y capacidad declarada."""
    user, taller = ctx
    return await service.actualizar_disponibilidad(user, taller.id, body, db)


@router.post(
    "/solicitudes/{solicitud_id}/asignar-tecnico-automatico",
    response_model=AsignarTecnicoOut,
    dependencies=[Depends(require_permission("tecnicos:asignar"))],
)
async def asignar_tecnico_automatico_route(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Asigna el primer técnico disponible del taller (FIFO)."""
    user, taller = ctx
    result = await service.asignar_tecnico_automatico(
        user, taller.id, solicitud_id, db
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay técnicos disponibles en el taller en este momento.",
        )
    return result


@router.post(
    "/solicitudes/{solicitud_id}/asignar-tecnico",
    response_model=AsignarTecnicoOut,
    dependencies=[Depends(require_permission("tecnicos:asignar"))],
)
async def asignar_tecnico(
    solicitud_id: int,
    body: AsignarTecnicoIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU28 — asignar o reasignar técnico del taller a la solicitud."""
    user, taller = ctx
    return await service.asignar_tecnico_a_solicitud(user, taller.id, solicitud_id, body, db)


@router.get(
    "/solicitudes/{solicitud_id}/asignaciones",
    response_model=list[AsignacionTecnicoRead],
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def listar_asignaciones_tecnico(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Historial de asignaciones de técnico para la solicitud (mismo taller)."""
    _, taller = ctx
    return await service.listar_asignaciones_tecnico(taller.id, solicitud_id, db)


@router.get(
    "/historial-atenciones",
    response_model=list[HistorialAtencionRead],
    dependencies=[Depends(require_permission("historial_atenciones:leer"))],
)
async def historial_atenciones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
    estado: EstadoSolicitudSeguimientoEnum | None = Query(None),
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
):
    """CU30 — solicitudes atendidas por este taller (filtros opcionales por fecha y estado)."""
    _, taller = ctx
    return await service.listar_historial_atenciones(
        taller.id, db, estado=estado, desde=desde, hasta=hasta, limit=limit
    )


@router.get(
    "/comisiones/resumen",
    response_model=ResumenComisionesRead,
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def resumen_comisiones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU31 — totales de comisiones del taller."""
    _, taller = ctx
    return await service.obtener_resumen_comisiones(taller.id, db)


@router.get(
    "/comisiones",
    response_model=list[ComisionTallerRead],
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def listar_comisiones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU31 — listado de comisiones con datos del pago asociado si existe."""
    _, taller = ctx
    return await service.listar_comisiones_taller(taller.id, db)


# ── Schemas inline para sync-web (offline → solicitudes_emergencia) ───────────

class _OfflineEvWebIn(BaseModel):
    client_uuid: str
    solicitud_id: int
    tipo_evento: str
    payload: dict[str, Any] = {}
    registrado_local_en: str


class _SyncWebIn(BaseModel):
    eventos: list[_OfflineEvWebIn]


class _OfflineEvWebOut(BaseModel):
    client_uuid: str
    solicitud_id: int
    tipo_evento: str
    sincronizado: bool
    error: str | None = None


class _SyncWebOut(BaseModel):
    total: int
    sincronizados: int
    con_error: int
    detalle: list[_OfflineEvWebOut]


_log = logging.getLogger(__name__)

_ESTADOS_VALIDOS: set[str] = {e.value for e in EstadoSolicitudSeguimientoEnum}


@router.post(
    "/sync-web",
    response_model=_SyncWebOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def sync_offline_web_events(
    body: _SyncWebIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
) -> _SyncWebOut:
    """
    Ciclo 4 — Unificación offline web (Opción A).

    Procesa eventos capturados sin conexión por el portal web del taller y los
    aplica sobre las solicitudes_emergencia del flujo real.

    Tipos de evento soportados:
    - ESTADO_CAMBIADO : aplica el nuevo_estado sobre la solicitud.
    - TALLER_ACEPTO   : informa al frontend (la aceptación formal se hace
                        por cotizaciones; aquí solo se reconoce).
    - TALLER_RECHAZO  : igual que TALLER_ACEPTO — reconocimiento.
    - OBSERVACION     : sin cambio de BD; retorna ok (es un log local).
    """
    _, taller = ctx
    detalle: list[_OfflineEvWebOut] = []

    for ev in body.eventos:
        try:
            tipo = ev.tipo_evento.upper()

            if tipo == "ESTADO_CAMBIADO":
                nuevo_raw = ev.payload.get("estado_nuevo") or ev.payload.get("nuevo_estado")
                if not nuevo_raw or str(nuevo_raw).upper() not in _ESTADOS_VALIDOS:
                    raise ValueError(f"estado_nuevo inválido: {nuevo_raw!r}")

                res = await db.execute(
                    select(SolicitudEmergencia).where(
                        SolicitudEmergencia.id == ev.solicitud_id,
                        SolicitudEmergencia.taller_id == taller.id,
                    )
                )
                sol = res.scalar_one_or_none()
                if sol is None:
                    raise ValueError(f"Solicitud {ev.solicitud_id} no pertenece a este taller")

                nuevo_estado = EstadoSolicitudSeguimientoEnum(str(nuevo_raw).upper())
                sol.estado = nuevo_estado
                aplicar_timestamps_por_estado(sol, nuevo_estado, utc_now_naive())
                db.add(sol)
                await db.flush()

                # Notificar WS a suscriptores del canal de la solicitud
                await ws_manager.broadcast_to_incident(
                    ev.solicitud_id,
                    "ESTADO_CAMBIADO",
                    status=nuevo_estado.value,
                    message=f"Estado actualizado offline: {nuevo_estado.value}",
                    payload={"solicitud_id": ev.solicitud_id, "origen": "OFFLINE_WEB"},
                )

            # Para estos tipos solo reconocemos — la acción real se hace por cotizaciones
            elif tipo in {"TALLER_ACEPTO", "TALLER_RECHAZO", "OBSERVACION"}:
                _log.info("sync-web: evento %s reconocido (sin cambio BD) sol=%s", tipo, ev.solicitud_id)

            else:
                raise ValueError(f"tipo_evento desconocido: {tipo!r}")

            detalle.append(
                _OfflineEvWebOut(
                    client_uuid=ev.client_uuid,
                    solicitud_id=ev.solicitud_id,
                    tipo_evento=ev.tipo_evento,
                    sincronizado=True,
                    error=None,
                )
            )
        except Exception as exc:
            detalle.append(
                _OfflineEvWebOut(
                    client_uuid=ev.client_uuid,
                    solicitud_id=ev.solicitud_id,
                    tipo_evento=ev.tipo_evento,
                    sincronizado=False,
                    error=str(exc),
                )
            )

    await db.commit()
    ok = sum(1 for d in detalle if d.sincronizado)
    return _SyncWebOut(
        total=len(detalle),
        sincronizados=ok,
        con_error=len(detalle) - ok,
        detalle=detalle,
    )


@router.get(
    "/reportes/dashboard",
    response_model=ReporteTallerDashboardRead,
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def reporte_dashboard_taller(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
    desde: date | None = Query(
        None,
        description="Inicio de periodo (inclusive). Comisiones: filtra por `calculado_at`. Solicitudes: por `created_at`.",
    ),
    hasta: date | None = Query(
        None,
        description="Fin de periodo (inclusive).",
    ),
):
    """
    Resumen operativo e inteligencia financiera: totales de comisiones, neto agregado por técnico,
    conteo de solicitudes por estado y ofertas pendientes en bandeja.
    """
    _, taller = ctx
    return await service.obtener_reporte_dashboard_taller(
        taller.id, db, desde=desde, hasta=hasta
    )
