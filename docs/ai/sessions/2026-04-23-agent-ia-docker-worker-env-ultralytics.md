# Sesión 2026-04-23 — IA modular en Docker, `.env` y Ultralytics

## Objetivo

Dejar operativo el flujo **backend → `ai-inference` → YOLO** (detección COCO o **clasificación** con modelo entrenado en Colab) y documentar incidentes para quien continúe.

## Qué se hizo / aprendizajes

1. **Compose**
   - Servicio `ai-inference` con **perfil** `ai` en `docker-compose.yml` (no arranca sin `--profile ai`).
   - Override opcional `docker-compose.ai-custom-model.yml`: monta `backend/incidentes_emergencias_v1.pt` en `/models/...`, fuerza `YOLO_TASK=classify`, `YOLO_IMGSZ=224`.
   - Comando típico stack completo + modelo propio:  
     `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build`
   - Tras `down -v --rmi all`, el primer `up --build` es **lento** (build, Postgres hasta healthy, descarga de pesos en volumen de caché del worker).

2. **`.env` raíz (duplicados)**
   - Si `AI_ENABLED` / `AI_INFERENCE_BASE_URL` aparecen **dos veces**, muchos parsers dejan **gana la última línea** → `AI_ENABLED=false` o URL vacía → backend **503** (“inferencia deshabilitada”).
   - Debe existir **una sola** sección coherente, p. ej. `AI_ENABLED=true` y `AI_INFERENCE_BASE_URL=http://ai-inference:8080` para Docker en la misma red.

3. **Bug worker (Ultralytics reciente)**
   - En `services/ai-inference/app/main.py`, `_yolo_classify` asumía `probs.top5` como **tensor** (`.cpu().numpy()`).
   - En versiones actuales `top5` / `top5conf` pueden ser **listas** → `AttributeError: 'list' object has no attribute 'cpu'` → **500** en `/internal/vision/analyze` y **502** visto desde el backend público.
   - **Corrección:** normalizar a listas de int/float tanto si vienen como `list`, `tuple`, tensor o numpy.

4. **Verificación**
   - `POST /api/ai/images/analyze` con Bearer (permiso `ai:inferir`) → **200** y JSON con `modelo_deteccion: incidentes_emergencias_v1.pt` cuando se usa el override custom.

## Archivos tocados (referencia)

- `services/ai-inference/app/main.py` — `_yolo_classify` (manejo de `top5` / `top5conf`).
- `docker-compose.yml`, `docker-compose.ai-custom-model.yml` — definición del worker y override.
- `.env.example` — variables `AI_*`, `YOLO_*` (comentarios).
- `backend/*.pt` en `.gitignore` — pesos no versionados; el Colab exporta a `backend/incidentes_emergencias_v1.pt` localmente.

## Recordatorio para el siguiente agente

Tras cambiar código del worker, reconstruir/recreate del contenedor `ai-inference` para que la imagen lleve el parche:

`docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference`
