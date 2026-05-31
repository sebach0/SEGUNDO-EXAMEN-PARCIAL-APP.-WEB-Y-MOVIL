"""Envío FCM HTTP v1 vía firebase-admin (síncrono; invocar con asyncio.to_thread)."""
from __future__ import annotations

import logging

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

_log = logging.getLogger(__name__)
_initialized = False


def _ensure_firebase_app() -> bool:
    global _initialized
    if _initialized:
        return True
    if not settings.FCM_ENABLED:
        return False
    p = settings.firebase_credentials_file
    if p is None:
        _log.warning("FCM_ENABLED sin credenciales válidas (FIREBASE_CREDENTIALS_PATH).")
        return False
    try:
        cred = credentials.Certificate(str(p))
        firebase_admin.initialize_app(cred)
        _initialized = True
        return True
    except ValueError:
        # Ya existe una app por defecto (p. ej. reload uvicorn)
        _initialized = True
        return True
    except Exception as e:
        _log.exception("No se pudo inicializar Firebase Admin: %s", e)
        return False


def send_push_multicast_sync(
    registration_tokens: list[str],
    *,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> None:
    if not registration_tokens:
        return
    if not _ensure_firebase_app():
        return
    payload = {k: str(v) for k, v in (data or {}).items()}
    msg = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=payload,
        tokens=registration_tokens,
    )
    try:
        response = messaging.send_each_for_multicast(msg)
        _log.info(
            "FCM multicast enviado: success=%s failure=%s tokens=%s",
            response.success_count,
            response.failure_count,
            len(registration_tokens),
        )
        if response.failure_count:
            for idx, r in enumerate(response.responses):
                if r.success:
                    continue
                _log.warning("FCM fallo token[%s]: %s", idx, r.exception)
    except Exception:
        _log.exception("Fallo al enviar FCM multicast")
