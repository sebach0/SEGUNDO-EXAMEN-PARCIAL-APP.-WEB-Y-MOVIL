# Timestamps operativos y ETA — solicitudes_emergencia (KPIs, SLA, retraso).
from __future__ import annotations

from datetime import datetime

from app.modules.incidentes.emergencias.models import (
    CancelacionFaseEnum,
    EstadoSolicitudSeguimientoEnum,
    EtaOrigenEnum,
    SolicitudEmergencia,
)


def init_reportado_en(sol: SolicitudEmergencia, now: datetime) -> None:
    if sol.reportado_en is None:
        sol.reportado_en = now


def aplicar_timestamps_por_estado(
    sol: SolicitudEmergencia,
    nuevo: EstadoSolicitudSeguimientoEnum,
    now: datetime,
) -> None:
    """Actualiza columnas de ciclo de vida usadas por KPIs y SLA."""
    if nuevo in (
        EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
    ) and sol.asignado_en is None:
        sol.asignado_en = now
    if nuevo == EstadoSolicitudSeguimientoEnum.EN_CAMINO and sol.en_camino_en is None:
        sol.en_camino_en = now
    if nuevo == EstadoSolicitudSeguimientoEnum.EN_ATENCION:
        if sol.en_atencion_en is None:
            sol.en_atencion_en = now
        if sol.llegada_real_en is None:
            sol.llegada_real_en = now


def registrar_eta(
    sol: SolicitudEmergencia,
    minutos: int,
    origen: EtaOrigenEnum,
    now: datetime,
) -> None:
    sol.tiempo_estimado_min = minutos
    sol.eta_origen = origen.value
    sol.eta_actualizado_en = now


def inferir_cancelacion_fase(estado: EstadoSolicitudSeguimientoEnum) -> CancelacionFaseEnum:
    if estado in (
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
    ):
        return CancelacionFaseEnum.PRE_ASIGNACION
    if estado == EstadoSolicitudSeguimientoEnum.EN_CAMINO:
        return CancelacionFaseEnum.EN_CAMINO
    if estado == EstadoSolicitudSeguimientoEnum.EN_ATENCION:
        return CancelacionFaseEnum.EN_ATENCION
    return CancelacionFaseEnum.POST_ASIGNACION


def marcar_cancelacion(
    sol: SolicitudEmergencia,
    *,
    usuario_id: int,
    motivo: str,
    now: datetime,
    estado_anterior: EstadoSolicitudSeguimientoEnum,
) -> None:
    sol.estado = EstadoSolicitudSeguimientoEnum.CANCELADA
    sol.motivo_cancelacion = motivo.strip()
    sol.cancelado_en = now
    sol.cancelado_por_usuario_id = usuario_id
    sol.cancelacion_fase = inferir_cancelacion_fase(estado_anterior).value
    sol.taller_habia_llegado = estado_anterior in (
        EstadoSolicitudSeguimientoEnum.EN_ATENCION,
        EstadoSolicitudSeguimientoEnum.FINALIZADA,
    )
    sol.updated_at = now
