# Sesión 2026-04-26 — Identidades seed (Santa Cruz, cuentas naturales)

## Objetivo

Centralizar credenciales y datos “de prueba pero creíbles” para desarrollo: nombres bolivianos, Santa Cruz de la Sierra, teléfonos +591 plausibles, talleres con nombre comercial, contraseña corta única (`scdemo1`), dominios `*.sc-demo.test` / `*.lista.sc-demo.test`.

## Cambios

- Nuevo **`backend/app/seeds/identidades_demo_sc.py`** — fuente única (importada por `config.py` como defaults de `SEED_*`).
- **`dev_taller.py`** — coordenadas del taller principal en SC (antes coords de La Paz hardcodeadas).
- **`dev_demo_santa_cruz.py`** — centro mapa desde identidades; historial usa `SEED_TALLER_NOMBRE_COMERCIAL`.
- **`dev_demo_media_prioridad.py`** — segundo taller en Santa Cruz (coords norte); textos de notificaciones/chat más naturales.
- **`dev_stress_visual.py`** — clientes con nombres reales y emails derivados; barrios SC; tel. +59177021xxx.
- **`docker-compose.yml`** — defaults de compose alineados a Bolivia/Santa Cruz (sustituye +57 / La Paz).
- **`docker-compose.override.yml`** — `SEED_TECNICO_ON_START=true` en dev.
- `.env.example`, `backend/.env.example`, `README.md`, `docs/ai/*` actualizados.

## Migración mental

Quien tenía `.env` con `cli@test.com` / `cli123` debe actualizar a los nuevos valores (o definir sus propios `SEED_*`). BD existente: los usuarios viejos no se renombran solos; en volumen de dev suele bastar `docker compose down -v` y volver a sembrar.
