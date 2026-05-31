# Mapeos a schemas, validaciones de estado y utilidades de evidencia/ubicación.
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.incidentes.emergencias import repository
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
    TipoEvidenciaSolicitudEnum,
)
from app.modules.incidentes.emergencias.schemas import (
    SolicitudEmergenciaDetailRead,
    SolicitudEmergenciaRead,
    SolicitudEvidenciaRead,
    SolicitudHistorialEstadoRead,
    SolicitudSeguimientoRead,
    SolicitudUbicacionRead,
    TallerSeguimientoRead,
    TecnicoSeguimientoRead,
    UbicacionCreateIn,
)


def to_detail(s: SolicitudEmergencia) -> SolicitudEmergenciaDetailRead:
    base = SolicitudEmergenciaRead.model_validate(s)
    ubs = sorted(s.ubicaciones, key=lambda x: x.registrado_at, reverse=True)
    evs = sorted(s.evidencias, key=lambda x: x.created_at, reverse=True)
    return SolicitudEmergenciaDetailRead(
        **base.model_dump(),
        ubicaciones=[SolicitudUbicacionRead.model_validate(x) for x in ubs],
        evidencias=[SolicitudEvidenciaRead.model_validate(x) for x in evs],
    )


def require_registrada(s: SolicitudEmergencia) -> None:
    if s.estado != EstadoSolicitudSeguimientoEnum.REGISTRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La solicitud está en estado {s.estado.value} y no admite esta operación.",
        )


def to_seguimiento(s: SolicitudEmergencia) -> SolicitudSeguimientoRead:
    historial = sorted(s.historial_estados, key=lambda h: h.created_at)
    taller = TallerSeguimientoRead.model_validate(s.taller) if s.taller is not None else None
    tecnico: TecnicoSeguimientoRead | None = None
    if s.tecnico is not None and s.tecnico.usuario is not None:
        u = s.tecnico.usuario
        tecnico = TecnicoSeguimientoRead(
            id=s.tecnico.id,
            nombres=u.nombres,
            apellidos=u.apellidos,
            telefono=u.telefono,
        )
    tiene_ubic = bool(s.ubicaciones)
    tiene_foto = any(e.tipo == TipoEvidenciaSolicitudEnum.FOTO for e in s.evidencias)
    tiene_audio = any(e.tipo == TipoEvidenciaSolicitudEnum.AUDIO for e in s.evidencias)
    return SolicitudSeguimientoRead(
        solicitud_id=s.id,
        estado=s.estado,
        updated_at=s.updated_at,
        ai_payload=s.ai_payload,
        tiempo_estimado_min=s.tiempo_estimado_min,
        finalizada_at=s.finalizada_at,
        taller=taller,
        tecnico=tecnico,
        historial_estados=[SolicitudHistorialEstadoRead.model_validate(h) for h in historial],
        tiene_ubicacion_cliente=tiene_ubic,
        tiene_evidencia_foto=tiene_foto,
        tiene_evidencia_audio=tiene_audio,
        presupuesto_bob=s.presupuesto_bob,
        presupuesto_registrado_at=s.presupuesto_registrado_at,
    )


def ext_foto(mime: str | None, filename: str) -> str:
    low = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if low in ("jpg", "jpeg", "png", "webp"):
        return f".{low}" if low != "jpeg" else ".jpg"
    if mime:
        m = mime.split(";")[0].strip().lower()
        if m == "image/jpeg":
            return ".jpg"
        if m == "image/png":
            return ".png"
        if m == "image/webp":
            return ".webp"
    return ".jpg"


def ext_audio(mime: str | None, filename: str) -> str:
    low = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if low in ("m4a", "aac", "mp3", "wav", "webm", "ogg", "opus"):
        return f".{low}"
    if mime:
        m = mime.split(";")[0].strip().lower()
        if m in ("audio/mp4", "audio/m4a", "audio/x-m4a"):
            return ".m4a"
        if m == "audio/mpeg":
            return ".mp3"
        if m == "audio/webm":
            return ".webm"
    return ".m4a"


async def add_ubicacion_internal(
    db: AsyncSession,
    sol: SolicitudEmergencia,
    body: UbicacionCreateIn,
    now,
) -> None:
    if body.es_actual:
        await repository.clear_ubicacion_actual_for_solicitud(db, sol.id)
    await repository.insert_ubicacion(
        db,
        solicitud_id=sol.id,
        latitud=body.latitud,
        longitud=body.longitud,
        precision_metros=body.precision_metros,
        direccion_referencia=body.direccion_referencia,
        es_actual=body.es_actual,
        registrado_at=now,
    )
    sol.updated_at = now
