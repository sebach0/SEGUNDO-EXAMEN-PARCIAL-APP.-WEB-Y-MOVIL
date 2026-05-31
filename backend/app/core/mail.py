# Envío SMTP (MailHog en desarrollo). Sin dependencias extra: smtplib en hilo.
from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

_log = logging.getLogger(__name__)


def _send_sync(to_addr: str, subject: str, body_text: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to_addr
    # Evitar quoted-printable en URLs (codifica "=" como "=3D" y puede romper ?token=... al copiar/pegar).
    msg.set_content(body_text, subtype="plain", charset="utf-8", cte="8bit")

    if not settings.SMTP_HOST:
        _log.warning("SMTP_HOST vacío: no se envía correo a %s", to_addr)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS) as smtp:
        if settings.SMTP_USE_TLS:
            context = ssl.create_default_context()
            smtp.starttls(context=context)
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        smtp.send_message(msg)


async def send_plain_email(to_addr: str, subject: str, body_text: str) -> None:
    """Envía un correo de texto plano (no bloquea el event loop)."""
    if not settings.EMAIL_ENABLED:
        _log.info("[EMAIL desactivado] to=%s subject=%s\n%s", to_addr, subject, body_text[:500])
        return
    try:
        await asyncio.to_thread(_send_sync, to_addr, subject, body_text)
    except Exception:
        _log.exception("Error enviando correo SMTP a %s", to_addr)
        if settings.EMAIL_STRICT:
            raise
