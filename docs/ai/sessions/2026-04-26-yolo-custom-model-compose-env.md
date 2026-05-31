# Sesión: YOLO custom — `.env` y volumen alineados con `incidentes_emergencias_v1.pt`

**Fecha:** 2026-04-26

## Problema

El usuario reportó que el modelo entrenado (`backend/incidentes_emergencias_v1.pt`) “ya no reconocía” aunque antes sí.

## Causa raíz

1. El worker `ai-inference` elige tarea y pesos con `YOLO_TASK` y `YOLO_MODEL`. Con **`YOLO_TASK=detect`** (default del YAML si no se define) y **`YOLO_MODEL=yolov8n.pt`**, Ultralytics corre **detección COCO** (persona, coche, etc.), no las clases del entrenamiento por carpetas (YOLOv8-cls).
2. El archivo `.pt` en el host **no** estaba en el contenedor a menos que se usara el override `docker-compose.ai-custom-model.yml` o un volumen equivalente: la ruta `/models/incidentes_emergencias_v1.pt` no existía dentro del contenedor con solo el `docker-compose.yml` base anterior.

## Cambio aplicado

- **`.env` (raíz):** `YOLO_TASK=classify`, `YOLO_MODEL=/models/incidentes_emergencias_v1.pt`, `YOLO_IMGSZ=224` (típico de cls; detect usa 640).
- **Montaje del peso:** sigue haciéndose con **`docker-compose.ai-custom-model.yml`** (no en el compose base, para no romper `docker compose up` en repos sin el `.pt`).
- Rebuild del worker: `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference`.

## Cómo verificar

En la respuesta de `POST /api/ai/images/analyze` (o el worker `POST /internal/vision/analyze`), `modelo_deteccion` debe ser `incidentes_emergencias_v1.pt` y en `hallazgos` o `objetos_detectados` figurar el texto de clasificación con el nombre de clase del modelo (p. ej. `clasificación imagen (modelo propio): <clase>`).

## Sin peso local (clone limpio)

Levantar **solo** con `docker compose.yml` y en `.env` `YOLO_TASK=detect`, `YOLO_MODEL=yolov8n.pt`, `YOLO_IMGSZ=640`. No hace falta el override ni el archivo `.pt` en el host.
