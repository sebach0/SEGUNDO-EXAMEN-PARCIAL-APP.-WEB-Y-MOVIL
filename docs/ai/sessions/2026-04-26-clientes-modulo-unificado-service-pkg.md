# 2026-04-26 — Unificar `clientes` + `cliente_movil` en un solo módulo

## Resultado

- Eliminado el paquete `cliente_movil/`. Todo vive en **`app/modules/clientes/`**:
  - `models.py`, `schemas.py` (admin), `schemas_movil.py` (app móvil)
  - `router.py` — prefijo `/app/cliente` (sin cambio de URL)
  - **`service/`** — `helpers.py`, `acceso.py`, `registro_perfil.py`, `vehiculos_cliente.py`, `__init__.py` reexporta la API pública usada por otros módulos
- Imports externos: `from app.modules.clientes.service import …` (antes `cliente_movil.service`).
- Bitácora en registro/perfil: `modulo="clientes"` (antes `cliente_movil`).
