# Optimización del tiempo de build Docker

## Diagnóstico (causas reales en este repo)

| Área | Problema | Efecto |
|------|-----------|--------|
| **`ai-inference`** | `build.context: .` (raíz del repo) | Docker envía **todo** el árbol (mobile, frontend, backend, docs, `.git` pesado…) al daemon en cada build. Suele ser el mayor costo en **“transferring context”** y en invalidación. |
| **Backend** | `RUN chown -R appuser:appuser /app` tras `COPY . .` | En cada cambio de código se recorre todo el árbol con `chown` en capa separada: **CPU y tiempo** innecesarios. |
| **Backend** | `PIP_NO_CACHE_DIR=1` en el stage builder | No afecta el cache de capas de Docker, pero en **cache miss** de `pip install` evita caché interna de pip dentro del RUN (menos útil; se quitó para alinearse con builds estándar). |
| **Frontend** | `COPY . .` + `npm run build` | Normal en SPA: cualquier cambio en `src/` invalida la capa de build. Mitigar = **`.dockerignore` más agresivo** (hecho) y no copiar tests/e2e. |
| **Pesos IA** | `torch`, `ultralytics`, Whisper en `requirements.txt` del worker | **Primera** instalación `pip` siempre será lenta (red + compilación mínima). Mejora con cache de BuildKit o imagen base pre-publicada, no con reordenar COPY. |
| **Docker Desktop (Windows)** | Comentarios en Dockerfiles: sin `# syntax=docker/dockerfile:1` ni `--mount=type=cache` | Trade-off aceptado: evita fallos intermitentes del builder en algunos entornos. Los **planes opcionales** abajo asumen BuildKit cuando sea estable para vos. |

## Cambios ya aplicados en el repo

1. **`docker-compose.yml` — `ai-inference`:** `context: ./services/ai-inference`, `dockerfile: Dockerfile`. El contexto pasa a ser **solo** `requirements.txt` + `app/`.
2. **`services/ai-inference/Dockerfile`:** `COPY` relativos al nuevo contexto (`requirements.txt`, `app/`).
3. **`services/ai-inference/.dockerignore`:** ignora basura Python/git en ese contexto.
4. **`backend/Dockerfile`:** usuario creado antes del `COPY`; `COPY --chown=appuser:appuser . .` y **sin** `chown -R`.
5. **`backend/.dockerignore`:** `tests/`, `uploads/`, `firebase-credentials.json`, bases locales.
6. **`frontend/.dockerignore`:** specs, e2e, IDE, caches.

## Plan por fases (prioridad)

### Fase A — Rápidas, bajo riesgo (hechas arriba)

- [x] Contexto mínimo para `ai-inference`.
- [x] `COPY --chown` en backend.
- [x] `.dockerignore` en los tres contextos de build.

**Resultado esperado:** builds repetidos de `ai-inference` y pasos de contexto de backend/frontend notablemente más cortos; menos datos sensibles en el contexto.

### Fase B — CI y caché (cuando uses Linux CI o BuildKit estable)

- Habilitar **BuildKit** (`DOCKER_BUILDKIT=1`) y, si aplica, `RUN --mount=type=cache,target=/root/.cache/pip` en el stage builder de **backend** y **ai-inference** para acelerar **cache miss** de pip sin inflar capas finales.
- En GitHub Actions / similar: **registry cache** (`type=registry`) o `docker/build-push-action` con `cache-from` / `cache-to`.

### Fase C — Imágenes base o dependencias

- **Worker IA:** separar `requirements.txt` en `requirements-cpu.txt` + stage opcional GPU, o publicar una imagen base interna “con torch ya instalado” y hacer `FROM mi-registry/ai-base:1`.
- **Frontend:** si el `npm ci` domina el tiempo, caché de npm con BuildKit (`--mount=type=cache,target=/root/.npm`).

### Fase D — Arquitectura de desarrollo

- `docker compose watch` o montajes de volumen para **no rebuild** en cada cambio de Python/TS en dev (imagen base + código montado); reservar build de imagen para releases.

## Comandos útiles de verificación

```bash
# Ver tamaño del contexto que percibe el builder (BuildKit)
docker compose --profile ai build ai-inference --progress=plain 2>&1 | head -40

# Solo validar sintaxis de compose
docker compose config --quiet
```

## Frontend en Docker: `MAILHOG_WEB_URL` / `prebuild`

El script `frontend/scripts/sync-from-root-env.cjs` corre en `prebuild`. En la imagen Docker el contexto es solo `./frontend`, no existe el `.env` del monorepo. Solución: si `process.env.MAILHOG_WEB_URL` está definida (p. ej. por `ARG`/`ENV` en el Dockerfile), se usa sin leer archivo; `docker-compose.yml` pasa `build.args.MAILHOG_WEB_URL: ${MAILHOG_WEB_URL:-}` desde el `.env` raíz del host.

## Postgres: `db` unhealthy en el primer `up`

Si ves `dependency failed to start: container emergencias_db is unhealthy`, suele ser **carrera** entre init (scripts `01_*.sql`…`14_*.sql`) + reinicio de Postgres y el healthcheck. En `docker-compose.yml`, el servicio `db` define `healthcheck.start_period: 240s` para que los fallos de `pg_isready` en esa ventana no cuenten como unhealthy.

## Qué no optimiza este documento

- Primera descarga de imágenes base (`python:3.11-slim-bookworm`, `node:20-alpine`).
- Primera instalación completa de dependencias pesadas del worker (es inherente al stack).

## Trazabilidad

- Sesión sugerida: `docs/ai/sessions/YYYY-MM-DD-docker-build-speed.md` al adoptar Fase B en CI.
