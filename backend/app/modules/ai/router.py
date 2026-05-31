# Routers REST — prefijo /api/ai (registrado en main).
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.ai import repository as ai_repository
from app.modules.ai.schemas import (
    AssignmentRankIn,
    AssignmentRankOut,
    AudioTranscribeResponse,
    DeteccionObjeto,
    ImageAnalyzeBatchResponse,
    ImageAnalyzeItem,
    ImageAnalyzeResponse,
    ImageClarity,
    IncidentClassifyIn,
    IncidentClassifyOut,
    IncidentPrioritizeIn,
    IncidentPrioritizeOut,
    StructuredSummaryIn,
    StructuredSummaryOut,
)
from app.modules.ai.services import inference_client
from app.modules.ai.services.assignment_scorer import rank_talleres
from app.modules.ai.services.audio_extract import extract_from_transcription
from app.modules.ai.services.incident_classifier import classify_incident
from app.modules.ai.services.priority_engine import prioritize
from app.modules.ai.services.structured_summary import build_structured_summary
_log = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["IA — inferencia y reglas"])


def _friendly_batch_inference_error(exc: BaseException) -> str:
    """Mensaje legible para el cliente; el detalle técnico queda en logs."""
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 400:
            return (
                "No se pudo analizar esta imagen: el servicio de visión no pudo decodificarla "
                "(formato no admitido o archivo dañado). Prueba JPEG o PNG; si usas AVIF/HEIF, "
                "reconstruye el contenedor ai-inference con la imagen actual (soporte libheif)."
            )
        if code == 413:
            return "No se pudo analizar esta imagen: excede el tamaño permitido en inferencia."
        return f"No se pudo analizar esta imagen: el servicio de visión respondió HTTP {code}."
    return "No se pudo analizar esta imagen (error de inferencia o red). Revisa logs del backend."


def _image_analyze_failure_response(mensaje: str) -> ImageAnalyzeResponse:
    """Respuesta estable cuando una imagen del lote no pudo analizarse (formato, inferencia, etc.)."""
    return ImageAnalyzeResponse(
        hallazgos=[mensaje],
        claridad_imagen=ImageClarity.BAJA,
        confianza=0.0,
        objetos_detectados=[],
        modelo_deteccion=None,
    )


async def _analyze_image_bytes(
    *,
    raw: bytes,
    filename: str,
    content_type: str,
) -> ImageAnalyzeResponse:
    if len(raw) > settings.AI_MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Imagen demasiado grande.")
    data = await inference_client.call_analyze_image(raw, filename, content_type)

    clar = str(data.get("claridad_imagen") or data.get("claridad") or "MEDIA").upper()
    if clar not in ("BAJA", "MEDIA", "ALTA"):
        clar = "MEDIA"
    raw_objs = data.get("objetos_detectados") or []
    objetos: list[DeteccionObjeto] = []
    for o in raw_objs:
        if isinstance(o, dict) and o.get("etiqueta") is not None:
            objetos.append(
                DeteccionObjeto(
                    etiqueta=str(o["etiqueta"]),
                    confianza=max(0.0, min(1.0, float(o.get("confianza") or 0.0))),
                )
            )

    return ImageAnalyzeResponse(
        hallazgos=list(data.get("hallazgos") or []),
        claridad_imagen=ImageClarity(clar),
        confianza=max(0.0, min(1.0, float(data.get("confianza") or 0.0))),
        objetos_detectados=objetos,
        modelo_deteccion=data.get("modelo_deteccion"),
    )


def _require_inference_available() -> None:
    if settings.AI_INFERENCE_STUB:
        return
    if not settings.AI_ENABLED or not inference_client.inference_base_url():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inferencia IA deshabilitada. Configure AI_ENABLED=true y AI_INFERENCE_BASE_URL, "
            "o AI_INFERENCE_STUB=true para pruebas.",
        )


@router.post(
    "/audio/transcribe",
    response_model=AudioTranscribeResponse,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def transcribe_audio(
    file: UploadFile = File(...),
):
    _require_inference_available()
    raw = await file.read()
    if len(raw) > settings.AI_MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio demasiado grande.")
    try:
        data = await inference_client.call_transcribe_audio(
            raw,
            file.filename or "audio.bin",
            file.content_type or "application/octet-stream",
        )
    except Exception as e:
        _log.exception("transcribe_audio")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"Fallo inferencia audio: {e!s}") from e

    text = str(data.get("text") or "").strip()
    conf = float(data.get("confidence") or 0.0)
    conf = max(0.0, min(1.0, conf))
    ex = extract_from_transcription(text)
    return AudioTranscribeResponse(
        transcripcion=text,
        keywords=ex.keywords,
        confianza=conf,
        tipo_problema_mencionado=ex.tipo_problema_mencionado,
        urgencia_percibida=ex.urgencia_percibida,
        contexto_breve=ex.contexto_breve or None,
    )


@router.post(
    "/images/analyze",
    response_model=ImageAnalyzeResponse,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def analyze_image(
    file: UploadFile = File(...),
):
    _require_inference_available()
    raw = await file.read()
    try:
        return await _analyze_image_bytes(
            raw=raw,
            filename=file.filename or "image.bin",
            content_type=file.content_type or "application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        _log.exception("analyze_image")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"Fallo inferencia imagen: {e!s}") from e


@router.post(
    "/images/analyze-batch",
    response_model=ImageAnalyzeBatchResponse,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def analyze_images_batch(
    files: list[UploadFile] = File(...),
):
    _require_inference_available()
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Debe enviar al menos una imagen.")

    results: list[ImageAnalyzeItem] = []
    merged_hallazgos: list[str] = []
    confidence_total = 0.0
    clarity_points_total = 0
    clarity_points_map = {"BAJA": 1, "MEDIA": 2, "ALTA": 3}

    for idx, file in enumerate(files, start=1):
        raw = await file.read()
        fname = file.filename or f"image-{idx}.bin"
        ct = file.content_type or "application/octet-stream"
        try:
            parsed = await _analyze_image_bytes(raw=raw, filename=fname, content_type=ct)
        except HTTPException as e:
            if e.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
                _log.warning("analyze_images_batch evidencia_id=img-%s: %s", idx, e.detail)
                parsed = _image_analyze_failure_response(str(e.detail))
            else:
                raise
        except Exception as e:
            _log.warning("analyze_images_batch evidencia_id=img-%s falló: %s", idx, e, exc_info=True)
            parsed = _image_analyze_failure_response(_friendly_batch_inference_error(e))
        results.append(ImageAnalyzeItem(evidencia_id=f"img-{idx}", resultado=parsed))
        merged_hallazgos.extend(parsed.hallazgos)
        confidence_total += parsed.confianza
        clarity_points_total += clarity_points_map.get(parsed.claridad_imagen.value, 2)

    unique_hallazgos = list(dict.fromkeys(merged_hallazgos))
    count = len(results)
    avg_conf = confidence_total / count if count else 0.0
    avg_clarity_points = clarity_points_total / count if count else 2
    if avg_clarity_points < 1.5:
        avg_clarity = ImageClarity.BAJA
    elif avg_clarity_points < 2.5:
        avg_clarity = ImageClarity.MEDIA
    else:
        avg_clarity = ImageClarity.ALTA

    return ImageAnalyzeBatchResponse(
        imagenes=results,
        hallazgos_consolidados=unique_hallazgos,
        claridad_promedio=avg_clarity,
        confianza_promedio=round(max(0.0, min(1.0, avg_conf)), 2),
    )


@router.post(
    "/incidents/classify",
    response_model=IncidentClassifyOut,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def incidents_classify(body: IncidentClassifyIn):
    return classify_incident(body)


@router.post(
    "/incidents/structured-summary",
    response_model=StructuredSummaryOut,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def incidents_structured_summary(body: StructuredSummaryIn):
    return build_structured_summary(body)


@router.post(
    "/incidents/prioritize",
    response_model=IncidentPrioritizeOut,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def incidents_prioritize(body: IncidentPrioritizeIn):
    return prioritize(body)


@router.post(
    "/assignment/rank",
    response_model=AssignmentRankOut,
    dependencies=[Depends(require_permission("ai:inferir"))],
)
async def assignment_rank(
    body: AssignmentRankIn,
    db: AsyncSession = Depends(get_db),
):
    rows = await ai_repository.list_talleres_for_assignment(db)
    if not rows:
        return AssignmentRankOut(candidatos=[], mejor_taller_id=None)
    return rank_talleres(body, rows)
