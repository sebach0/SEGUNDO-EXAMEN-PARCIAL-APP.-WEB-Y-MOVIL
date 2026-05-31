# Sesión 2026-04-26 — Postgres `db` healthy en primer `up`

## Problema

`dependency failed to start: container emergencias_db is unhealthy`: carrera entre initdb + scripts SQL + reinicio de Postgres y `pg_isready` sin `start_period` en el healthcheck.

## Cambio

`docker-compose.yml` → servicio `db`: `healthcheck.start_period: 240s`, `retries: 12`.

## Referencias

- `docs/ai/DOCKER_BUILD_OPTIMIZATION.md` (sección Postgres).
- `DECISIONS_LOG.md` **DEC-019**.
