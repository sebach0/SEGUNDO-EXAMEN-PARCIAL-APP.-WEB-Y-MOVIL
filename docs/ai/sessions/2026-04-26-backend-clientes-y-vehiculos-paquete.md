# Sesión 2026-04-26 — Paquete `clientes_y_vehiculos`

## Hecho

- Directorio `app/modules/clientes_y_vehiculos/` con `__init__.py`.
- Movidos `clientes/` y `vehiculos/` como subpaquetes.
- Sustitución de imports: `app.modules.clientes` → `...clientes_y_vehiculos.clientes` (lookahead para no corromper `clientes_y_vehiculos`); `app.modules.vehiculos` → `...vehiculos`.
- `db_metadata.py`: orden conservado (`clientes` antes de `vehiculos` por FK en modelos).

## Verificación

- `python -m compileall -q app` desde `backend/`.

## Notas

- Rutas HTTP sin cambio (`/api/app/cliente`, `/api/vehiculos`, etc.).
