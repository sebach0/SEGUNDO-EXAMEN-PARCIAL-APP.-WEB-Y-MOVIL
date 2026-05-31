# Sesión 2026-04-26 — Paquete `talleres_y_tecnicos`

## Hecho

- Directorio `app/modules/talleres_y_tecnicos/` con `__init__.py`.
- Movidos:
  - `acceso_y_administracion/talleres` → `talleres_y_tecnicos/talleres`
  - `taller_responsable` → `talleres_y_tecnicos/taller_responsable`
  - `tecnico` → `talleres_y_tecnicos/tecnico`
- Reemplazo de imports en backend + `tests/test_tecnico_schemas.py`:
  - `app.modules.acceso_y_administracion.talleres` → `app.modules.talleres_y_tecnicos.talleres`
  - `app.modules.taller_responsable` → `app.modules.talleres_y_tecnicos.taller_responsable`
  - `app.modules.tecnico` → `app.modules.talleres_y_tecnicos.tecnico`

## Contrato HTTP

- Sin cambio de prefijos (`/api/talleres`, `/api/app/taller`, `/api/app/tecnico/emergencias`, etc.).

## Verificación

- `python -m compileall -q app` desde `backend/`.
