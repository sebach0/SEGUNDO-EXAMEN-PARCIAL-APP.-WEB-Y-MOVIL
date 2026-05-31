# Sesión 2026-04-25 — Seguimiento móvil (chips IA, ETA, FCM)

## Objetivo

Corregir chips del análisis asistido que mostraban "no" pese a tener medios, habilitar flujo de ETA desde taller, limpiar restos `(CU##)` en timeline, y foreground FCM.

## Cambios

- **Flutter:** `SolicitudSeguimiento` parsea `tiene_ubicacion_cliente`, `tiene_evidencia_foto`, `tiene_evidencia_audio`. `SolicitudAiResumenCard` acepta overrides; detalle y seguimiento los pasan. `SeguimientoTimeline` sanitiza `(CU\\d+)` en observaciones. `FcmMessageListener` + `app.dart`.
- **Angular:** `AsignarTecnicoPayload.tiempo_estimado_min` + campo en incidente detalle.
- **Backend:** ya estaba (sesión previa): flags en seguimiento y asignación con ETA.

## Notas

- Resumen de texto de IA puede seguir diciendo "GPS no confirmado" si el snapshot no se regenera; los chips son la fuente de presencia de medios.
- `google-services.json` no está en el repo; cada dev lo coloca en `android/app/`.
