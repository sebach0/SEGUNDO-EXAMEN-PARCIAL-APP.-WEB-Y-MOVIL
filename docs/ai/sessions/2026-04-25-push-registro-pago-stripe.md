# Sesión 2026-04-25 — Push en registro cliente + pago confirmado

## Objetivo

1. Enviar push al cliente cuando su cuenta quede activa en dispositivo (primer token FCM).
2. Enviar push al cliente cuando el pago de la solicitud se confirme, incluyendo Stripe.
3. Confirmar uso de variables Stripe: `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`.

## Implementación

- **`backend/app/modules/comunicaciones/service.py`**
  - `registrar_fcm_token`: si el usuario cliente no tenía tokens previos, crea notificación/push de bienvenida (`SOLICITUD_CREADA`).

- **`backend/app/modules/pagos/service.py`**
  - Se integra `comunicaciones_service.notificar_cliente_solicitud_emergencia(...)`.
  - `_aplicar_resultado_pasarela(...)`: al marcar `PAGADO` en flujo simulado, dispara push.
  - `confirmar_pago_stripe(...)`: al confirmar `succeeded`, dispara push.

## Stripe

- `STRIPE_SECRET_KEY`: usado para crear y consultar PaymentIntent.
- `STRIPE_PUBLISHABLE_KEY`: devuelto al móvil en `PagoIniciadoRead` para PaymentSheet.

## Validación

- `python -m py_compile app/modules/comunicaciones/service.py app/modules/pagos/service.py` ✅
