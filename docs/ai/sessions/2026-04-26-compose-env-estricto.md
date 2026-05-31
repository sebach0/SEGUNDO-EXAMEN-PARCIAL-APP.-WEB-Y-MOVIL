# Sesión 2026-04-26 — Compose estricto + `.env.example` completo

## Objetivo

Que las líneas de `docker-compose.yml` que antes interpolaban con `:-default` para infra compartida pasen a depender explícitamente del `.env` raíz, y que `.env.example` documente cada clave nueva.

## Cambios (evolución)

- Primera iteración: `TZ`/`PGTZ`/`POSTGRES_HOST`/`FIREBASE_CREDENTIALS_PATH`/`BACKEND_UPSTREAM` sin fallback en YAML.
- Ajuste posterior: **restaurar fallbacks** en Compose para esas variables de infra (Bolivia, `db`, `/app/firebase-credentials.json`, `backend:8000`) para que proyectos con `.env` incompleto no reciban strings vacíos ni warnings ruidosos; **`.env.example` sigue listando** las claves explícitas como referencia.

## Verificación

`docker compose config` debe completar; con `.env` alineado a `.env.example`, sin sorpresas en TZ ni nginx upstream.
