# Helpers y constantes compartidos — bandeja, asignaciones, disponibilidad.
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, SolicitudEmergencia
from app.modules.atencion.taller_emergencias import repository
from app.modules.atencion.taller_emergencias.models import SolicitudAsignacionTecnico, TallerDisponibilidad
from app.modules.atencion.taller_emergencias.schemas import (
    AsignacionTecnicoRead,
    AsignarTecnicoOut,
    BandejaIncidenteBaseRead,
    SolicitudBandejaDetalleRead,
    SolicitudEvidenciaTallerRead,
)
from app.modules.talleres_y_tecnicos.talleres.models import Tecnico

_BASE_KEYS = frozenset(BandejaIncidenteBaseRead.model_fields.keys())

ESTADOS_PERMITE_ASIGNAR_TECNICO = frozenset(
    (
        EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
    )
)


def extract_nivel_prioridad(ai_payload: dict | None) -> str | None:
    if not ai_payload or not isinstance(ai_payload, dict):
        return None
    pr = ai_payload.get("prioridad")
    if not isinstance(pr, dict):
        return None
    n = pr.get("nivel_prioridad")
    return n if isinstance(n, str) else None


def enrich_row(row: dict) -> dict:
    r = dict(row)
    r["nivel_prioridad"] = extract_nivel_prioridad(r.get("ai_payload"))
    return r


def row_to_list_item(row: dict) -> BandejaIncidenteBaseRead:
    r = enrich_row(row)
    slim = {k: r[k] for k in _BASE_KEYS if k in r}
    return BandejaIncidenteBaseRead.model_validate(slim)


def row_to_detalle(row: dict, evidencias: list) -> SolicitudBandejaDetalleRead:
    r = enrich_row(row)
    slim = {k: r[k] for k in _BASE_KEYS if k in r}
    return SolicitudBandejaDetalleRead(
        **slim,
        estado_bandeja=row["estado_bandeja"],
        motivo_rechazo=row.get("motivo_rechazo"),
        creado_at=row["bandeja_creado_at"],
        respondido_at=row.get("respondido_at"),
        evidencias=[SolicitudEvidenciaTallerRead.model_validate(x) for x in evidencias],
    )


async def ensure_disponibilidad(db: AsyncSession, taller_id: int) -> TallerDisponibilidad:
    row = await repository.get_disponibilidad(db, taller_id=taller_id)
    if row is not None:
        return row
    now = utc_now_naive()
    return await repository.insert_disponibilidad_default(db, taller_id=taller_id, updated_at=now)


def estado_terminal_solicitud(estado: EstadoSolicitudSeguimientoEnum) -> bool:
    return estado in (
        EstadoSolicitudSeguimientoEnum.FINALIZADA,
        EstadoSolicitudSeguimientoEnum.CANCELADA,
    )


def tecnico_disponible_para_asignar(t: Tecnico) -> bool:
    if t.disponibilidad is None:
        return True
    d = t.disponibilidad.strip().lower()
    if d in ("no", "no_disponible", "ausente", "ocupado"):
        return False
    return True


def to_asignacion_read(row: SolicitudAsignacionTecnico) -> AsignacionTecnicoRead:
    return AsignacionTecnicoRead.model_validate(row)


def to_asignar_out(se: SolicitudEmergencia, asignacion: SolicitudAsignacionTecnico) -> AsignarTecnicoOut:
    return AsignarTecnicoOut(
        solicitud_id=se.id,
        estado_solicitud=se.estado,
        tecnico_id=se.tecnico_id,
        tecnico_asignado_at=se.tecnico_asignado_at,
        asignacion=to_asignacion_read(asignacion),
    )
