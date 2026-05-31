# Sesión 2026-04-26 — Seed stress visual (catálogos + clientes extra)

## Objetivo

Cubrir el ítem **no crítico**: más datos de catálogo vehículo y cuentas cliente adicionales para **stress visual** (pickers, listados admin, pruebas manuales).

## Implementación

- `backend/app/seeds/dev_catalogos_vehiculo.py` — función `ensure_catalogos_vehiculo_stress_extra`: tipos Van/Minibús/Rural y 8 marcas con 3 modelos cada una (idempotente).
- `backend/app/seeds/dev_stress_visual.py` — `ensure_stress_visual_seed`: catálogo extra + hasta 8 clientes con nombres SC y emails `*.lista.sc-demo.test`; tel. `+59177021xxx`; contraseña por defecto `scdemo1` (`identidades_demo_sc` / `SEED_STRESS_CLIENT_PASSWORD`).
- `__main__.py`, `main.py` (lifespan opcional `SEED_STRESS_VISUAL_ON_START`), `config.py`, `.env.example` raíz y `backend/.env.example`, `README.md`.

## Uso

Tras `python -m app.seeds`, ejemplo: `valentina.suarez.01@lista.sc-demo.test` / `scdemo1` (ver `stress_cliente_email` en `identidades_demo_sc.py`).
