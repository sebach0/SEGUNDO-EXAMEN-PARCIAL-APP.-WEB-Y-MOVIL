# Sesión 2026-04-26 — Paquete `incidentes` / submódulo `emergencias`

## Hecho

- `backend/app/modules/incidentes/__init__.py` (contexto CU11–CU18).
- `backend/app/modules/emergencias/` → `backend/app/modules/incidentes/emergencias/`.
- Reemplazo global `app.modules.emergencias` → `app.modules.incidentes.emergencias` en backend (incl. tests).

## Contrato HTTP

- Sin cambios: rutas bajo `/api/app/cliente/emergencias` (y routers anidados de pagos/comunicaciones que comparten prefijo).

## Verificación

- `python -m compileall -q app` desde `backend/`.
