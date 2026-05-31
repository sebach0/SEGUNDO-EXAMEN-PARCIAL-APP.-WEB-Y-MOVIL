# Pipeline IA tras crear solicitud (reglas + inferencia opcional).
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutil import utc_now_naive
from app.modules.ai import repository as ai_repository
from app.modules.ai.schemas import (
    AssignmentRankIn,
    IncidentCategory,
    IncidentClassifyIn,
    IncidentPrioritizeIn,
    StructuredSummaryIn,
    UbicacionResumenIn,
)
from app.modules.ai.services import inference_client
from app.modules.ai.services.assignment_scorer import rank_talleres
from app.modules.ai.services.incident_classifier import classify_incident
from app.modules.ai.services.priority_engine import prioritize
from app.modules.ai.services.structured_summary import build_structured_summary
from app.modules.incidentes.emergencias import repository as emergencias_repository
from app.modules.incidentes.emergencias.models import TipoEvidenciaSolicitudEnum

_log = logging.getLogger(__name__)


async def enrich_solicitud_ai_after_create(
    db: AsyncSession,
    *,
    solicitud_id: int,
    cliente_id: int,
) -> None:
    """Best-effort: no aborta el alta de solicitud si falla."""
    try:
        await _enrich_solicitud_ai_after_create_impl(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    except Exception:
        _log.exception("enrich_solicitud_ai_after_create falló para solicitud_id=%s", solicitud_id)


async def _enrich_solicitud_ai_after_create_impl(
    db: AsyncSession,
    *,
    solicitud_id: int,
    cliente_id: int,
) -> None:
    s = await emergencias_repository.get_solicitud_for_cliente(
        db,
        solicitud_id=solicitud_id,
        cliente_id=cliente_id,
        with_children=True,
    )
    if s is None:
        return

    descripcion = (s.descripcion_texto or "").strip()
    ubic = None
    if s.ubicaciones:
        actuales = [u for u in s.ubicaciones if u.es_actual]
        ubic = actuales[0] if actuales else max(s.ubicaciones, key=lambda x: x.registrado_at)

    transcripcion: str | None = None
    hallazgos_por_imagen: list[list[str]] = []
    hallazgos: list[str] = []

    if settings.AI_ENABLED or settings.AI_INFERENCE_STUB:
        for ev in sorted(s.evidencias, key=lambda x: x.created_at, reverse=True):
            if ev.tipo == TipoEvidenciaSolicitudEnum.AUDIO and ev.archivo_url:
                raw = await inference_client.call_transcribe_from_url(ev.archivo_url)
                if raw and raw.get("text"):
                    transcripcion = str(raw["text"]).strip() or None
                    break
        for ev in sorted(s.evidencias, key=lambda x: x.created_at):
            if ev.tipo != TipoEvidenciaSolicitudEnum.FOTO or not ev.archivo_url:
                continue
            try:
                loaded = await inference_client.load_evidencia_bytes(ev.archivo_url)
                if not loaded:
                    continue
                content, ct = loaded
                vis = await inference_client.call_analyze_image(
                    content,
                    ev.nombre_archivo or "foto.jpg",
                    ct if ct.startswith("image/") else "image/jpeg",
                )
                hlist = list(vis.get("hallazgos") or [])
                hallazgos_por_imagen.append(hlist)
            except Exception:
                _log.debug("Análisis de imagen omitido para evidencia", exc_info=True)
        hallazgos = [h for sub in hallazgos_por_imagen for h in sub]

    cls_in = IncidentClassifyIn(
        texto_cliente=descripcion or None,
        transcripcion_audio=transcripcion,
        hallazgos_vision=hallazgos,
        hallazgos_vision_por_imagen=hallazgos_por_imagen,
    )
    cls_out = classify_incident(cls_in)

    pri_in = IncidentPrioritizeIn(
        texto_cliente=descripcion or None,
        transcripcion_audio=transcripcion,
        hallazgos_vision=hallazgos,
        hallazgos_vision_por_imagen=hallazgos_por_imagen,
        categoria=cls_out.categoria,
        direccion_referencia=ubic.direccion_referencia if ubic else None,
    )
    pri_out = prioritize(pri_in)

    ubi_in = None
    if ubic:
        ubi_in = UbicacionResumenIn(
            latitud=ubic.latitud,
            longitud=ubic.longitud,
            direccion_referencia=ubic.direccion_referencia,
        )

    summary_in = StructuredSummaryIn(
        texto_cliente=descripcion or None,
        transcripcion_audio=transcripcion,
        hallazgos_vision=hallazgos,
        hallazgos_vision_por_imagen=hallazgos_por_imagen,
        categoria=cls_out.categoria,
        ubicacion=ubi_in,
    )
    summary_out = build_structured_summary(summary_in)

    asignacion = None
    if ubic:
        taller_rows = await ai_repository.list_talleres_for_assignment(db)
        if taller_rows:
            asignacion = rank_talleres(
                AssignmentRankIn(
                    incident_lat=ubic.latitud,
                    incident_lng=ubic.longitud,
                    categoria=cls_out.categoria,
                    nivel_prioridad=pri_out.nivel_prioridad,
                    ciudad_incidente=None,
                ),
                taller_rows,
            )

    payload: dict = {
        "version": 1,
        "clasificacion": cls_out.model_dump(),
        "prioridad": pri_out.model_dump(),
        "resumen_estructurado": summary_out.model_dump(),
    }
    if transcripcion:
        payload["transcripcion_audio"] = transcripcion
    if hallazgos:
        payload["hallazgos_vision"] = hallazgos
    if hallazgos_por_imagen:
        payload["hallazgos_vision_por_imagen"] = hallazgos_por_imagen
    if asignacion is not None:
        payload["sugerencia_asignacion"] = asignacion.model_dump()

    now = utc_now_naive()
    await emergencias_repository.update_solicitud_ai_payload(
        db,
        solicitud_id=solicitud_id,
        payload=payload,
        updated_at=now,
    )
