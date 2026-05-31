# Sesión IA — Fase 1 Incidentes Compuestos

Fecha: 2026-04-25

## Objetivo
Soportar incidentes reales con múltiples daños y múltiples evidencias (texto + audio + varias fotos) sin Kubernetes, sobre el stack actual con Docker Compose.

## Cambios aplicados

1. **Schemas IA ampliados**
   - Inputs nuevos: `transcripciones_audio[]`, `hallazgos_vision_por_imagen[]`.
   - Output ampliado en clasificación: `damages[]`, `requires_manual_review`, `conflict_notes`.
   - Output ampliado en priorización: `score`, `damages_considerados[]`.
   - Output ampliado en resumen: `danos_detectados[]`.
   - Nuevo contrato batch de imágenes: `ImageAnalyzeBatchResponse`.

2. **Fusionador multimodal v1**
   - Archivo: `backend/app/modules/ai/services/evidence_fusion.py`.
   - Pesos iniciales:
     - imagen: 0.45
     - texto: 0.30
     - audio: 0.25
   - Incluye:
     - agregación multi-foto,
     - cálculo de severidad por daño,
     - detección de conflictos y bandera de revisión manual.

3. **Router IA**
   - Se mantiene `POST /api/ai/images/analyze` (compatibilidad).
   - Nuevo `POST /api/ai/images/analyze-batch` para `files[]`.

4. **Servicios de negocio IA**
   - `incident_classifier`: usa fusionador y devuelve `damages[]`.
   - `priority_engine`: consume evidencia compuesta y devuelve score + daños considerados.
   - `structured_summary`: sintetiza daños múltiples en el resumen y retorna `danos_detectados[]`.

5. **Pruebas**
   - `backend/tests/test_ai_engines.py` incorpora:
     - clasificación multi-daño consistente,
     - priorización compuesta,
     - resumen estructurado con daños compuestos.

## Resultado

- El backend queda listo para triage de incidentes compuestos en Fase 1.
- No se rompió el flujo existente: endpoints previos se mantienen.
- Se habilita evolución a Fase 2 (modelo multi-label entrenado) con contrato ya preparado.
