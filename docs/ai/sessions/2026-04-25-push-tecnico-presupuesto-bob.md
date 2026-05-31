# Sesión 2026-04-25 — Push técnico + presupuesto BOB + diagnóstico FCM

## Objetivo

- Notificar al **técnico** (in-app + FCM) cuando el taller le **asigna** una emergencia.
- Permitir que el técnico indique **presupuesto en BOB** al pasar a **EN_ATENCION** y que el **cliente** lo vea en seguimiento.
- Dejar trazas en logs cuando FCM no puede enviar por **falta de tokens**.

## Diagnóstico FCM (mismo dispositivo, dos roles)

`usuario_fcm_tokens.token` es **único**: el último usuario que registra el token “se queda” con el envío. En los logs del usuario, el cliente borró el token al cerrar sesión y el técnico registró el **mismo** token; los pushes de taller asignado / técnico asignado iban al usuario que tuviera el token al momento del envío. Para probar **cliente + técnico** a la vez: dos dispositivos o dos cuentas en dos teléfonos.

## Implementación

- **Backend:** `notificar_tecnico_solicitud_emergencia` en `comunicaciones/service.py`; llamada desde `portal_taller_emergencias/service.py` tras notificar al cliente en `asignar_tecnico_a_solicitud`. `_notificar_push` loguea `INFO` si no hay tokens.
- **Migración:** `0014_presupuesto_bob_solicitud.sql` — columnas `presupuesto_bob`, `presupuesto_registrado_at` en `solicitudes_emergencia`. Montada en `docker-compose.yml` como init `14_...` (BD **nueva**). Volúmenes ya existentes: aplicar SQL manualmente.
- **API técnico:** `PATCH .../estado` acepta `presupuesto_bob` obligatorio si `nuevo_estado=EN_ATENCION`; mensaje al cliente incluye el monto.
- **Mobile:** modelo seguimiento + pantalla seguimiento (tarjeta BOB); técnico: diálogo de monto al marcar “En atención”; repositorio envía `presupuesto_bob`; tarjeta de lista muestra presupuesto si existe.

## Pasarela de pago

Stripe y lógica en `backend/app/modules/pagos/` (`router.py`, `service.py`, `stripe_client.py`); variables `STRIPE_*` en `.env`.
