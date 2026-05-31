# Sesión: `ai_payload` con OTROS aunque hubiera foto — re-enriquecer tras evidencia/ubicación

**Fecha:** 2026-04-27

## Síntoma

En la app móvil, solicitud creada con texto mínimo ("Si") + foto del choque: la ficha mostraba **Otros (53%)**, `fuentes` solo `texto`, resumen con **ubicación GPS no confirmada** aunque luego se enviaron GPS e imagen.

## Causa

1. **`enrich_solicitud_ai_after_create` solo se llamaba al `POST` de crear solicitud**, cuando aún no existían evidencias ni ubicación en muchos flujos (wizard: texto → otras pantallas → foto). El `ai_payload` quedaba fijado con clasificación **solo por texto** → `OTROS`.
2. Tras subir FOTO, **no se volvía a ejecutar** el pipeline de IA.
3. Al analizar la imagen, el backend hacía `httpx.get(ev.archivo_url)` con URL pública tipo `http://192.168.0.143:8000/...` — desde el contenedor **no siempre** es fiable; conviene leer el archivo en `uploads/evidencias/` cuando la URL contiene `/media/evidencias/<nombre>`.

## Cambio

- `inference_client.load_evidencia_bytes`: lee primero ruta local bajo `evidencias_upload_dir`, si no existe intenta HTTP.
- `call_transcribe_from_url` usa `load_evidencia_bytes` (mismo criterio para audio).
- `post_create._enrich_solicitud_ai_after_create_impl`: todas las FOTOS en orden, `hallazgos_vision_por_imagen` + fusión; sin `httpx` directo a la URL de la imagen.
- Tras **agregar evidencia** (URL o archivo), **agregar ubicación** y **actualizar texto** de la solicitud: `await enrich_solicitud_ai_after_create(...)` para refrescar `ai_payload`.

## Verificación

Crear solicitud, subir foto, abrir de nuevo el detalle: `clasificacion.fuentes` debe incluir **imagen** si el worker analizó la foto; categoría y daños deberían reflejar visión (según reglas + modelo YOLO).

## Swagger 401

`POST /api/ai/images/analyze` requiere JWT real (`Authorization: Bearer <access_token>`), no el email. Obtener token vía `POST /api/auth/login` con usuario que tenga `ai:inferir` (p. ej. admin tras seeds).
