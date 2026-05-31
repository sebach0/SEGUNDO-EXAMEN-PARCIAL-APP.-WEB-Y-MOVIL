# Sesión 2026-04-22 — Documentación: columna `tecnico_asignado_at`

## Contexto

El móvil fallaba al registrar emergencias (HTTP 500) por `UndefinedColumnError: tecnico_asignado_at` en `solicitudes_emergencia`.

## Cambio en código / infra (resumen)

- `0003_ciclo2_fase2_seguimiento.sql`: `ADD COLUMN IF NOT EXISTS tecnico_asignado_at`.
- `0006_tecnico_asignado_at.sql`: parche idempotente; montado en `docker-compose` como quinto script de init.
- Bases ya inicializadas: aplicar `0006` o `ALTER TABLE` equivalente una vez.

## Docs actualizados

- `CURRENT_STATE.md`, `DECISIONS_LOG.md` (DEC-009), `HANDOFF_LATEST.md`, `NEXT_STEPS.md`, `ARCHITECTURE.md` (sección migraciones).
