# Evidencias FOTO/AUDIO por URL o subida directa (CU13/CU14).
from __future__ import annotations

import asyncio
import uuid

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutil import utc_now_naive
from app.modules.ai.services.post_create import enrich_solicitud_ai_after_create
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias import repository
from app.modules.incidentes.emergencias.models import TipoEvidenciaSolicitudEnum
from app.modules.incidentes.emergencias.schemas import EvidenciaCreateIn, SolicitudEmergenciaDetailRead
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import helpers


async def agregar_evidencia(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    body: EvidenciaCreateIn,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    s = await repository.get_solicitud_for_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    helpers.require_registrada(s)

    now = utc_now_naive()
    await repository.insert_evidencia(
        db,
        solicitud_id=s.id,
        tipo=body.tipo,
        archivo_url=body.archivo_url.strip(),
        mime_type=body.mime_type,
        nombre_archivo=body.nombre_archivo,
        tamano_bytes=body.tamano_bytes,
        created_at=now,
    )
    s.updated_at = now

    await registrar_accion(
        db,
        "emergencias",
        "solicitud_evidencias",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Evidencia tipo {body.tipo.value}",
        usuario_id=user.id,
        entidad_id=solicitud_id,
    )

    await enrich_solicitud_ai_after_create(db, solicitud_id=solicitud_id, cliente_id=cliente_id)

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)


async def agregar_evidencia_archivo(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    request: Request,
    tipo: TipoEvidenciaSolicitudEnum,
    file: UploadFile,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    """CU13/CU14 — sube el binario al servidor y guarda URL pública bajo /api/media/evidencias/."""
    s = await repository.get_solicitud_for_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    helpers.require_registrada(s)

    raw = await file.read()
    if len(raw) > settings.EVIDENCIA_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande (máx. {settings.EVIDENCIA_MAX_UPLOAD_BYTES} bytes).",
        )

    mime = (file.content_type or "").split(";")[0].strip().lower() or None
    fname = (file.filename or "upload").replace("\\", "/").split("/")[-1]
    safe_fname = "".join(c for c in fname if c.isalnum() or c in "._-")[:120] or "upload"

    if tipo == TipoEvidenciaSolicitudEnum.FOTO:
        if mime and not mime.startswith("image/") and mime != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para FOTO el archivo debe ser image/* (o application/octet-stream desde la cámara).",
            )
        ext = helpers.ext_foto(mime, safe_fname)
    else:
        if mime and not mime.startswith("audio/") and mime not in (
            "application/octet-stream",
            "video/mp4",
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para AUDIO el archivo debe ser audio/*.",
            )
        ext = helpers.ext_audio(mime, safe_fname)

    stored = f"{uuid.uuid4().hex}{ext}"
    dest_dir = settings.evidencias_upload_dir
    dest_path = dest_dir / stored

    await asyncio.to_thread(dest_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(dest_path.write_bytes, raw)

    ev_base = (settings.EVIDENCIAS_PUBLIC_BASE_URL or "").strip()
    api_pub = (settings.API_PUBLIC_URL or "").strip()
    base = (ev_base or api_pub or str(request.base_url)).rstrip("/")
    pfx = settings.API_PREFIX if settings.API_PREFIX.startswith("/") else f"/{settings.API_PREFIX}"
    public_url = f"{base}{pfx}/media/evidencias/{stored}"

    now = utc_now_naive()
    await repository.insert_evidencia(
        db,
        solicitud_id=s.id,
        tipo=tipo,
        archivo_url=public_url,
        mime_type=mime,
        nombre_archivo=safe_fname,
        tamano_bytes=len(raw),
        created_at=now,
    )
    s.updated_at = now

    await registrar_accion(
        db,
        "emergencias",
        "solicitud_evidencias",
        AccionBitacoraEnum.CREAR,
        descripcion=f"Evidencia archivo tipo {tipo.value}",
        usuario_id=user.id,
        entidad_id=solicitud_id,
    )

    await enrich_solicitud_ai_after_create(db, solicitud_id=solicitud_id, cliente_id=cliente_id)

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)
