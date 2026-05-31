# 2026-04-26 — Dominio `clientes`, renombre módulos `portal_*` y rutas `/app/*`

## Qué se hizo

1. **ORM `Cliente`** movido de `usuarios/models.py` a `app/modules/clientes/models.py` (dominio cliente). `Usuario` mantiene la relación 1:1 por nombre de clase SQLAlchemy. `db_metadata` importa `clientes` tras `usuarios`. Schemas admin `ClienteCreate` / `ClienteRead` en `clientes/schemas.py`; `usuarios/router` los importa desde ahí.
2. **Paquetes renombrados** (sin prefijo `portal_`):
   - `portal_cliente` → `cliente_movil`
   - `portal_taller` → `taller_responsable`
   - `portal_tecnico` → `tecnico_movil`
   - `portal_taller_emergencias` → `taller_emergencias`
   - `portal_tecnico_emergencias` → `tecnico_emergencias`
3. **Rutas HTTP**: prefijo `/portal/...` sustituido por **`/app/...`** en backend, Flutter (`api_constants.dart` + getters `app*`) y Angular (interceptor + servicios taller).
4. **Bitácora / módulos string**: `portal_*` → nombres alineados (`cliente_movil`, `taller_responsable`, `taller_emergencias`, `tecnico_emergencias`).
5. **Tests** renombrados: `test_taller_emergencias_schemas.py`, `test_tecnico_emergencias_schemas.py`, `test_taller_emergencias_fase4_schemas.py`.

## Ruptura de contrato

Cualquier cliente que llamara `/api/portal/...` debe usar **`/api/app/...`** (con el mismo `API_PREFIX`).

## Verificación local

- `python -m compileall -q app` en `backend/` (sin venv FastAPI en este host, solo sintaxis).
