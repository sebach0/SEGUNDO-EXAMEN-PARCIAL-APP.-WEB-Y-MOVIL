# 2026-04-26 — Pagos: comisiones taller al confirmar pago

## Problema

Los pagos quedaban `PAGADO` en `pagos`, pero el dashboard del taller (`/reportes/dashboard`, resumen de `comisiones_taller`) seguía en 0 porque **no** se insertaba fila en `comisiones_taller`.

## Solución

- `registrar_comision_taller_tras_pago` en `backend/app/modules/pagos_y_comisiones/pagos/repository.py`: calcula 10 % comisión y neto al taller (misma lógica que `dev_demo_santa_cruz`); idempotente si ya existe comisión para la `solicitud_id`.
- Llamadas desde `service.py`: `_aplicar_resultado_pasarela` (pasarela simulada) y `confirmar_pago_stripe`.

## Nota

Pagos confirmados **antes** de este cambio no tienen comisión; si hace falta, backfill manual según `solicitud_id` / `taller_id` / `monto` en `pagos`.
