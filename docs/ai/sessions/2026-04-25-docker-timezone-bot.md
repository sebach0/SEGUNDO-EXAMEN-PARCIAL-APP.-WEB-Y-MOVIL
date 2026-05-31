# Sesión 2026-04-25 — Docker timezone BOT

## Objetivo

Alinear fecha/hora de contenedores Docker a **Santa Cruz, Bolivia** para logs y procesos internos.

## Cambios

- `docker-compose.yml`:
  - `db`: `TZ=America/La_Paz` + `PGTZ=America/La_Paz`
  - `mailhog`: `TZ=America/La_Paz`
  - `backend`: `TZ=America/La_Paz`
  - `frontend`: `TZ=America/La_Paz`
  - `ai-inference`: `TZ=America/La_Paz`

## Validación

- `docker compose config` ✅

## Nota

La estrategia final queda así:

- **Persistencia**: backend/DB pueden seguir en UTC si aplica.
- **Presentación**: web/mobile forzadas a BOT.
- **Contenedores**: reloj/logs en BOT para operación local coherente.
