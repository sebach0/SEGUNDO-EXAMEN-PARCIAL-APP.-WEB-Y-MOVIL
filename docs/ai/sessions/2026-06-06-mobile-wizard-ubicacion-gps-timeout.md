# Sesión: fix congelamiento Paso 2 ubicación — wizard emergencias mobile

## Problema
Al pulsar **Enviar ubicación actual** en el wizard de emergencias (paso 2), la app parecía congelarse.

## Causa
`Geolocator.getCurrentPosition()` sin `timeLimit` puede bloquearse indefinidamente (emulador Android sin GPS simulado, GPS lento, permisos pendientes). El overlay `_busy` cubría toda la pantalla sin mensaje.

## Solución
- Nuevo util `mobile/lib/core/utils/geolocation_helper.dart` → `obtainDevicePosition()` con timeout 12s, fallback a `getLastKnownPosition()`, mensaje claro si falla.
- `emergencia_wizard_screen.dart`: usa el helper en enviar/preview; overlay muestra `_busyLabel` ("Obteniendo GPS…").

## Prueba manual
1. Emulador: Extended Controls → Location → punto fijo.
2. Wizard emergencia → paso 2 → **Enviar ubicación actual**.
3. Debe completar en ≤12s o mostrar error útil (no quedar colgado).
