"""
Cliente Stripe (síncrono). Ejecutar desde el servicio con ``anyio.to_thread.run_sync``
para no bloquear el event loop de FastAPI.
"""
from __future__ import annotations

from typing import Any

import stripe


def crear_payment_intent(
    *,
    secret_key: str,
    amount_minor_units: int,
    currency: str,
    metadata: dict[str, str],
) -> dict[str, Any]:
    stripe.api_key = secret_key
    pi = stripe.PaymentIntent.create(
        amount=amount_minor_units,
        currency=currency.lower(),
        automatic_payment_methods={"enabled": True},
        metadata=metadata,
    )
    return {
        "id": pi.id,
        "client_secret": pi.client_secret,
        "status": getattr(pi, "status", None) or "",
    }


def obtener_payment_intent(*, secret_key: str, payment_intent_id: str) -> dict[str, Any]:
    stripe.api_key = secret_key
    pi = stripe.PaymentIntent.retrieve(payment_intent_id)
    return {
        "id": pi.id,
        "status": pi.status,
        "amount_received": getattr(pi, "amount_received", None),
    }
