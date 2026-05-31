# Sesión 2026-04-26 — AVIF + analyze-batch resiliente

## Problema
`POST /api/ai/images/analyze-batch` con JPEG + AVIF: las dos primeras inferencias 200, la tercera 400 en `ai-inference` (`Imagen no válida.`), backend 502 y lote abortado.

## Causa
OpenCV `imdecode` no lee AVIF; `PIL.Image.open` sin soporte HEIF/AVIF falla igual en la imagen `.avif`.

## Cambios
- `services/ai-inference/requirements.txt`: `pillow-heif==0.16.0`
- `services/ai-inference/Dockerfile`: paquete `libheif1`
- `services/ai-inference/app/main.py`: `register_heif_opener()` tras import
- `backend/app/modules/ai/router.py`: `_image_analyze_failure_response`; batch captura excepciones por archivo; `analyze_image` (una foto) sigue devolviendo 502 ante fallo de inferencia.

## Verificación
Rebuild contenedores `ai-inference` y `backend`, repetir lote con las mismas tres imágenes → 200 y tres entradas en `imagenes[]`.
