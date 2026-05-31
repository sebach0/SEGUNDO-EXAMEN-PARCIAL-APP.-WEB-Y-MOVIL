# Cliente HTTP hacia el contenedor ai-inference.
from __future__ import annotations

import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings

_log = logging.getLogger(__name__)


def _local_evidencia_file(archivo_url: str) -> Path | None:
    """Si la URL apunta a /api/.../media/evidencias/<file>, devuelve ruta en disco si existe."""
    path = urlparse(archivo_url).path
    marker = "/media/evidencias/"
    if marker not in path:
        return None
    name = path.split(marker, 1)[1].split("?")[0].strip()
    if not name or "/" in name or ".." in name:
        return None
    local = settings.evidencias_upload_dir / name
    return local if local.is_file() else None


async def load_evidencia_bytes(archivo_url: str) -> tuple[bytes, str] | None:
    """
    Lee el binario de una evidencia ya subida: primero archivo local (evita HTTP a IP del móvil
    desde Docker), si no, GET a la URL.
    """
    p = _local_evidencia_file(archivo_url)
    if p is not None:

        def _read() -> tuple[bytes, str]:
            data = p.read_bytes()
            mime, _ = mimetypes.guess_type(str(p))
            return data, (mime or "application/octet-stream")

        return await asyncio.to_thread(_read)
    timeout = httpx.Timeout(settings.AI_INFERENCE_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            r = await client.get(archivo_url)
            r.raise_for_status()
        except Exception as e:
            _log.warning("No se pudo descargar evidencia para IA: %s", e)
            return None
        ct = (r.headers.get("content-type") or "application/octet-stream").split(";")[0].strip()
        return (r.content, ct)


def inference_base_url() -> str | None:
    u = (settings.AI_INFERENCE_BASE_URL or "").strip().rstrip("/")
    return u or None


async def call_transcribe_audio(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:
    if settings.AI_INFERENCE_STUB:
        return {
            "text": "mi auto no enciende y creo que es batería",
            "confidence": 0.91,
            "vad_has_voice": True,
        }
    base = inference_base_url()
    if not base or not settings.AI_ENABLED:
        raise RuntimeError("Inferencia IA deshabilitada o AI_INFERENCE_BASE_URL no configurada.")

    url = f"{base}/internal/audio/transcribe"
    timeout = httpx.Timeout(settings.AI_INFERENCE_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            url,
            files={"file": (filename, file_bytes, content_type or "application/octet-stream")},
        )
        resp.raise_for_status()
        return resp.json()


async def call_analyze_image(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:
    if settings.AI_INFERENCE_STUB:
        return {
            "hallazgos": ["posible llanta pinchada", "daño visible lateral"],
            "claridad_imagen": "MEDIA",
            "confianza": 0.76,
            "objetos_detectados": [
                {"etiqueta": "persona", "confianza": 0.82},
                {"etiqueta": "automóvil", "confianza": 0.77},
            ],
            "modelo_deteccion": "stub",
        }
    base = inference_base_url()
    if not base or not settings.AI_ENABLED:
        raise RuntimeError("Inferencia IA deshabilitada o AI_INFERENCE_BASE_URL no configurada.")

    url = f"{base}/internal/vision/analyze"
    timeout = httpx.Timeout(settings.AI_INFERENCE_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            url,
            files={"file": (filename, file_bytes, content_type or "application/octet-stream")},
        )
        resp.raise_for_status()
        return resp.json()


async def call_transcribe_from_url(audio_url: str) -> dict[str, Any] | None:
    """Obtiene bytes (local o HTTP) y transcribe (p. ej. evidencia ya subida)."""
    if settings.AI_INFERENCE_STUB:
        return await call_transcribe_audio(b"\x00\x00", "stub.wav", "audio/wav")
    if not settings.AI_ENABLED:
        return None
    loaded = await load_evidencia_bytes(audio_url)
    if not loaded:
        return None
    data, ct = loaded
    return await call_transcribe_audio(data, "evidencia.bin", ct)
