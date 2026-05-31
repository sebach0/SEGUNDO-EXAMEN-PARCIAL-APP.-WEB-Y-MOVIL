# Sesión 2026-04-26 — Paquete `atencion` / `taller_emergencias`

## Hecho

- `app/modules/atencion/__init__.py`.
- Movido `taller_emergencias` → `atencion/taller_emergencias/`.
- Reemplazo global `app.modules.taller_emergencias` → `app.modules.atencion.taller_emergencias` (backend + tests).

## Contrato HTTP

- Sin cambio: prefijo `/api/app/taller/emergencias`.

## Verificación

- `python -m compileall -q app` desde `backend/`.
