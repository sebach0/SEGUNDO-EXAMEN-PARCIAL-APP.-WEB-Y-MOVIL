# Sesión 2026-04-25 — Hora Santa Cruz unificada (sistema)

## Objetivo

Forzar que la hora mostrada al usuario sea consistentemente **Bolivia Santa Cruz (BOT, UTC-4)** en web y mobile.

## Cambios aplicados

- **Angular**
  - `frontend/src/app/app.config.ts`:
    - `LOCALE_ID = 'es-BO'`
    - `DATE_PIPE_DEFAULT_OPTIONS.timezone = '-0400'`
  - `frontend/src/main.ts`:
    - `registerLocaleData(localeEsBo)`

- **Mobile Flutter**
  - Se reutiliza `mobile/lib/core/utils/bolivia_time.dart`.
  - Se migraron pantallas/widgets que aún usaban `.toLocal()`:
    - `seguimiento_timeline.dart`
    - `eta_llegada_card.dart`
    - `emergencia_ubicacion_tecnico_screen.dart`
    - `comprobante_simple_card.dart`
    - `notificacion_list_item.dart`
    - `notificacion_detalle_screen.dart`
    - `emergencias_mis_solicitudes_screen.dart`

## Verificación

- `flutter analyze` (mobile) ✅
- `npm run build` (frontend) ✅

## Decisión técnica

Se mantiene backend con timestamps de sistema/UTC y se normaliza BOT en **presentación** para no romper persistencia ni integraciones.
