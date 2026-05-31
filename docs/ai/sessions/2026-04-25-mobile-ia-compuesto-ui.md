# Sesión AI — 2026-04-25 — Mobile IA compuesto UI

## Objetivo
Reflejar en mobile cliente los nuevos campos del `ai_payload` generado por la fase compuesta (multi-foto/multi-daño), especialmente en detalle y seguimiento.

## Cambios aplicados
- `mobile/lib/cliente/emergencias/domain/solicitud_ai_payload.dart`
  - Parseo agregado para:
    - `hallazgos_vision_por_imagen`
    - `clasificacion.damages`
    - `clasificacion.requires_manual_review`
    - `clasificacion.conflict_notes`
    - `prioridad.score`
    - `prioridad.damages_considerados`
    - `resumen_estructurado.danos_detectados`
- `mobile/lib/cliente/emergencias/presentation/widgets/ai/solicitud_ai_resumen_card.dart`
  - UI extendida para mostrar:
    - daños IA y daños considerados
    - score de prioridad
    - nota de revisión manual
    - notas de conflicto
    - daños detectados en resumen
    - hallazgos por imagen

## Resultado
La tarjeta de análisis asistido ya no queda limitada al payload v1 básico y ahora puede reflejar análisis compuesto sin cambios adicionales de navegación o repositorio.

## Riesgos / pendientes
- Aún falta (si se desea) disparar explícitamente `POST /api/ai/images/analyze-batch` desde mobile en flujo wizard; en esta sesión se resolvió el puente de **consumo y visualización**.
