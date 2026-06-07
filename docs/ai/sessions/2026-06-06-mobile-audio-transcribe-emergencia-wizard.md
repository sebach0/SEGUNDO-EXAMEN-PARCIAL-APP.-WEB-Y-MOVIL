# Sesión 2026-06-06 — Audio → texto en wizard de emergencia (mobile)

## Objetivo
Permitir que el cliente, al crear una solicitud de emergencia, grabe audio y lo convierta automáticamente en texto editable.

## Implementación

### Backend (sin cambios)
- Se reutiliza `POST /api/ai/audio/transcribe` (`app/modules/ai/router.py`).
- Permiso requerido: `ai:inferir` (rol CLIENTE ya lo tiene vía migración `0012_ia_modulo.sql`).
- Requiere `AI_ENABLED=true` + perfil Docker `ai`, o `AI_INFERENCE_STUB=true` para pruebas.

### Mobile
- `lib/cliente/emergencias/domain/audio_transcribe_models.dart` — modelo `AudioTranscribeResult`.
- `lib/cliente/emergencias/data/ai_transcribe_repository.dart` — multipart al endpoint IA.
- `ApiConstants.aiAudioTranscribe` + provider `aiTranscribeRepositoryProvider`.
- `emergencia_wizard_screen.dart`:
  - **Paso 1:** botón «Grabar descripción por voz» → transcribe → rellena descripción inicial.
  - **Paso 4:** al grabar evidencia audio → transcribe → agrega texto al relato → sube archivo.
  - Tarjeta «Transcripción del audio» con confianza y botones «Usar como descripción/detalle».
  - Offline: el audio se guarda en cola; la transcripción requiere red (mensaje al usuario).

## Cómo probar
1. `docker compose --profile ai up -d` con `AI_ENABLED=true`.
2. Login cliente en mobile, wizard emergencia.
3. Paso 1: grabar voz → ver texto en campo descripción.
4. Paso 4: grabar audio → ver tarjeta transcripción + evidencia subida.

## Pendiente opcional
- Transcribir audios de la cola offline al sincronizar (hoy el backend ya enriquece `ai_payload` post-subida).
