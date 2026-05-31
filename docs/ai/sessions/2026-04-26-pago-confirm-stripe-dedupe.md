# Sesión 2026-04-26 — Pago: confirmar sin duplicar intent + Stripe PI

## Problema

- Tras elegir método, el flujo volvía a llamar `iniciarPago` en confirmar → varios `POST /pagos` y 422 en `confirmar-stripe` por falta de `payment_intent_id` / mismatch con `referencia_externa`.

## Cambio

- `mobile/lib/cliente/pagos/presentation/screens/pago_confirmacion_screen.dart`
  - `_coherentPagoIniciado`: reutiliza `draft.pagoIniciado` si coincide `solicitudId`, `MetodoPago` y monto (ε 0,02).
  - Stripe: exige `pago.stripePaymentIntentId` y pasa `paymentIntentId: pi` a `confirmarStripe`.

## Pendiente ajenos a este parche

- FCM en técnico: token único en BD → mismo dispositivo con dos cuentas reasigna el token; considerar flujo "un rol activo" o múltiples filas con `plataforma+device_id` (diseño).
- Seeders más ricos: backlog.
