# Sesión 2026-04-25 — Docker build estable + fix backend `max_digits`

## Contexto
- Se reportó falla intermitente de build Docker: `frontend grpc server closed unexpectedly`.
- Luego de estabilizar Dockerfiles, el stack levantó pero backend cayó al iniciar con:
  `ValueError: Unknown constraint max_digits` en `portal_tecnico_emergencias/schemas.py`.

## Cambios aplicados
- `backend/Dockerfile` y `frontend/Dockerfile`:
  - removido `# syntax=docker/dockerfile:1`
  - removido `RUN --mount=type=cache`
- `backend/app/modules/portal_tecnico_emergencias/schemas.py`:
  - `presupuesto_bob` mantiene `gt=0`
  - se retiraron `max_digits` y `decimal_places` del `Field`
  - validación monetaria (máx. 12 dígitos, 2 decimales) movida a `@model_validator`

## Validación
- `python -m py_compile app/modules/portal_tecnico_emergencias/schemas.py` ✅
- `docker compose ... up -d --build backend` ✅
- Logs backend: startup completo + `/health` 200 ✅

## Nota operativa
- No es necesario “construir dos veces” como regla.
- Si falla `db unhealthy` en primer `up`, inspeccionar `docker compose logs db` y reintentar cuando Postgres termine init.
