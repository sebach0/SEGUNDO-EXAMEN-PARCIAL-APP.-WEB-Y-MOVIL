# Sesión 2026-04-25 — Técnico mobile (hora BOT, tipo incidente, push)

## Objetivo

Mejorar la experiencia del técnico con:

1. Hora consistente de Bolivia (Santa Cruz) en toda la UI de técnico.
2. Mostrar tipo de incidente y prioridad/gravedad en “Servicios asignados”.
3. Mejorar push con navegación al tocar la notificación.

## Cambios implementados

- **Backend técnico:** `ServicioAsignadoRead` ahora incluye `categoria_incidente` y `nivel_prioridad`; repositorio extrae ambos desde `solicitudes_emergencia.ai_payload` (`clasificacion.categoria_incidente` y `prioridad.nivel_prioridad`).
- **Mobile técnico dominio/UI:** `ServicioAsignadoTecnico` parsea nuevos campos; tarjeta lista y detalle muestran chips/bloque de incidente. Prioridad alta/crítica se presenta como “grave”.
- **Hora BOT:** nuevo util `mobile/lib/core/utils/bolivia_time.dart` (UTC-4) aplicado en:
  - `tecnico_servicio_card.dart`
  - `tecnico_servicio_detalle_screen.dart`
  - `tecnico_servicio_ubicacion_screen.dart`
  - `chat_bubble.dart` (también impacta chat cliente/técnico)
- **Push:** `FcmMessageListener` ahora:
  - escucha `onMessageOpenedApp`,
  - maneja `getInitialMessage`,
  - enruta por `solicitud_id` y `tipo` a chat o detalle.

## Validación

- `flutter analyze` en `mobile/` ✅
- `python -m py_compile` en backend técnico (schemas/repository) ✅

## Pendiente recomendado

- Confirmar payload FCM en producción para tipos adicionales y ampliar routing.
- Añadir pruebas de integración para deep-link en push (cliente y técnico).
