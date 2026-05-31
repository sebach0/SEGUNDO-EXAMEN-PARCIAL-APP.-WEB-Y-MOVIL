# Sesión 2026-04-26 — Seed demo media prioridad

## Objetivo

Completar el bloque de **media prioridad** sobre el demo Santa Cruz: comunicaciones (in-app + chat), `ai_payload` rico para UI/bandeja, disponibilidad del taller principal y **segundo taller en Santa Cruz** con bandeja en solicitudes `[DEMO-SC]` ya existentes.

## Implementación

- `backend/app/seeds/dev_demo_media_prioridad.py` — idempotencia vía notificación gate `[DEMO-MEDIA] seed v1` para el usuario cliente seed.
- `backend/app/seeds/__main__.py` — llama `ensure_demo_media_prioridad(..., require_enabled_flag=False)` después de Santa Cruz.
- `backend/app/core/config.py` — `SEED_DEMO_MEDIA_PRIORIDAD_ON_START`, `SEED_TALLER2_*`.
- `backend/app/main.py` — lifespan: condición OR + ejecución si `SEED_DEMO_MEDIA_PRIORIDAD_ON_START`.
- `backend/.env.example`, `.env.example` raíz — documentación mínima de variables.

## Uso

```bash
docker compose exec backend python -m app.seeds
```

Segundo taller (por defecto, ver `identidades_demo_sc.py`): `rodrigo.torrez@sc-demo.test` / `scdemo1` (sobreescribible con `SEED_TALLER2_*`).

## Notas

- Si no existen solicitudes `[DEMO-SC]`, el módulo registra warning y no inserta datos dependientes de ellas.
- Tipos de notificación limitados al enum Postgres (`0004_ciclo2_fase3_comunicaciones.sql`).
