# Detección de retraso y recálculo operativo de ETA (flujo solicitudes_emergencia).
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
)


def _referencia_eta_inicio(sol: SolicitudEmergencia) -> datetime | None:
    """Momento desde el cual corre el ETA (asignación o salida en camino)."""
    return sol.en_camino_en or sol.asignado_en or sol.tecnico_asignado_at


def minutos_retraso(sol: SolicitudEmergencia, now: datetime | None = None) -> int | None:
    """
    Minutos que el servicio lleva por encima del ETA publicado.
    None si no hay ETA o aún no aplica el reloj.
    """
    if sol.tiempo_estimado_min is None or sol.tiempo_estimado_min <= 0:
        return None
    if sol.estado not in (
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.EN_CAMINO,
    ):
        return None
    inicio = _referencia_eta_inicio(sol)
    if inicio is None:
        return None
    now = now or utc_now_naive()
    limite = inicio + timedelta(minutes=int(sol.tiempo_estimado_min))
    if now <= limite:
        return 0
    return int((now - limite).total_seconds() // 60)


def eta_limite_en(sol: SolicitudEmergencia) -> datetime | None:
    inicio = _referencia_eta_inicio(sol)
    if inicio is None or sol.tiempo_estimado_min is None:
        return None
    return inicio + timedelta(minutes=int(sol.tiempo_estimado_min))


async def emit_eta_actualizado_ws(sol: SolicitudEmergencia) -> None:
    """Difunde ETA actualizado por WebSocket (canal = solicitud_id)."""
    if sol.id is None or sol.tiempo_estimado_min is None:
        return
    from app.modules.ciclo4.websocket.manager import manager as ws_manager

    await ws_manager.broadcast_to_incident(
        sol.id,
        "ETA_ACTUALIZADO",
        status=sol.estado.value if sol.estado else None,
        message=f"ETA actualizado: {sol.tiempo_estimado_min} min",
        payload={
            "solicitud_id": sol.id,
            "tiempo_estimado_min": sol.tiempo_estimado_min,
            "eta_origen": sol.eta_origen,
            "eta_actualizado_en": sol.eta_actualizado_en.isoformat()
            if sol.eta_actualizado_en
            else None,
        },
    )


async def emit_servicio_retrasado_ws(
    sol: SolicitudEmergencia,
    *,
    retraso_min: int,
) -> None:
    if sol.id is None:
        return
    from app.modules.ciclo4.websocket.manager import manager as ws_manager

    await ws_manager.broadcast_to_incident(
        sol.id,
        "SERVICIO_RETRASADO",
        status=sol.estado.value if sol.estado else None,
        message=f"Servicio con retraso de {retraso_min} min",
        payload={
            "solicitud_id": sol.id,
            "minutos_retraso": retraso_min,
            "tiempo_estimado_min": sol.tiempo_estimado_min,
        },
    )


async def evaluar_y_notificar_retraso(
    db: AsyncSession,
    sol: SolicitudEmergencia,
    *,
    now: datetime | None = None,
    umbral_min: int = 5,
) -> bool:
    """
    Si hay retraso >= umbral_min y aún no se notificó, avisa al cliente.
    Retorna True si se envió notificación.
    """
    now = now or utc_now_naive()
    retraso = minutos_retraso(sol, now)
    if retraso is None or retraso < umbral_min:
        return False
    if sol.retraso_notificado_en is not None:
        return False

    sol.retraso_notificado_en = now
    from app.modules.comunicacion_y_notificaciones.notificaciones import service as notif_service
    from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum

    await notif_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=sol,
        tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
        titulo="Auxilio demorado",
        mensaje=(
            f"El técnico lleva aproximadamente {retraso} min de retraso "
            f"respecto al tiempo estimado ({sol.tiempo_estimado_min} min). "
            "Seguimos monitoreando tu solicitud."
        ),
    )
    await emit_servicio_retrasado_ws(sol, retraso_min=retraso)
    return True
