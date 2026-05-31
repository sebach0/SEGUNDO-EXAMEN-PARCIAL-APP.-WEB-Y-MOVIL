# Sesión — Seed demo Santa Cruz (alta prioridad)

## Qué se agregó

- Módulo `backend/app/seeds/dev_demo_santa_cruz.py`:
  - 4 vehículos demo (placas únicas) con marcas/modelos del catálogo y referencias a zonas de **Santa Cruz de la Sierra** (Equipetrol, Urbarí, 2do anillo, doble vía La Guardia, etc.).
  - 10 solicitudes `[DEMO-SC]` con estados variados, bandeja (PENDIENTE, ACEPTADA, RECHAZADA, EXPIRADA), historial, ubicación, evidencia foto (URL HTTPS), asignaciones técnico (incl. reasignación demo), dos flujos **FINALIZADA + pago PAGADO + comisión CALCULADA** (890 y 1245,50 BOB).
- `python -m app.seeds` ejecuta `ensure_demo_santa_cruz_datos(..., require_enabled_flag=False)` al final (siempre que existan cliente/taller/técnico seed).
- `SEED_DEMO_SANTA_CRUZ_ON_START` en `config.py` + `.env.example` para opcionalmente correr el mismo seed en el **lifespan** del backend junto con otros `SEED_*_ON_START`.
- Defaults de ciudad seed cliente/taller → Santa Cruz de la Sierra.

## Idempotencia

- Si ya hay ≥10 solicitudes con descripción `LIKE '[DEMO-SC]%'` para el cliente seed, no inserta de nuevo.
- Vehículos por placa única: no duplica.

## Comando

```bash
docker compose exec backend python -m app.seeds
```
